'use client';
import { useState, useEffect, useRef, useMemo } from 'react';

/**
 * TechnicalGlossary — Full interactive simulation glossary.
 * Embeds directly inside God Mode and Facilitator dashboards.
 * Renders LaTeX via MathJax 3 (loaded once on mount).
 *
 * Clusters:
 *   I.  Financial Metrics
 *   II. Sustainability & ESG
 *   III. Strategic Positioning
 */

// --- Glossary data (30 terms across 3 clusters) ----------------------------

const CLUSTERS = [
  {
    id: 'fi',
    number: '01',
    tag: 'Cluster I',
    title: 'Financial Metrics',
    desc: 'The quantitative ledger of corporate resource allocation, profitability, and firm value across the simulation\'s 10-round arc.',
    accentColor: '#4ca8c9',
    terms: [
      {
        id: 'csf',
        name: 'Corporate Strategic Fund (CSF)',
        abbr: 'CSF / Treasury',
        keywords: 'corporate strategic fund treasury csf opex revenue dividends loan capital',
        definition: 'The master liquidity pool of the conglomerate, representing the net accumulated surplus after all revenue, operational expenditures, capital deployments, and dividend payments have been settled. It is the primary resource constraint governing every subsequent round decision.',
        logic: 'Computed in engine.py ? calc_csf() and persisted to global_round_states.corporate_treasury. A short-term loan is auto-triggered if total CAPEX exceeds 20% of the opening treasury, at an interest rate of 12%. Dividends are clamped to the treasury balance (VULN-001) and total CAPEX is capped at 2× treasury (VULN-006).',
        formula: `$$\\text{CSF}_{t+1} = \\text{Treasury}_t + \\sum_{i=1}^{n}\\left(\\text{Revenue}_i - \\text{OPEX}_i\\right) - \\text{Dividends}$$
$$\\text{If } \\text{CAPEX}_{\\Sigma} > 0.20 \\cdot \\text{Treasury}_t:\\quad \\text{Loan} = \\text{CAPEX}_{\\Sigma} - 0.20\\cdot\\text{Treasury}_t,\\quad \\text{Penalty} = \\text{Loan} \\times 0.12$$`,
        significance: 'For a CFO or CEO, the CSF is the only permissive gate for all decisions. Teams that over-invest early trigger forced loans that compound as hidden OPEX drains in subsequent rounds. The 20% rule simulates real-world capital discipline: firms that deploy >20% of liquidity into single periods face escalating cost-of-capital penalties. Managing treasury velocity—not just its absolute level—is the defining financial skill of the simulation.',
      },
      {
        id: 'ebitda',
        name: 'Terminal EBITDA (Year T0+5 Horizon)',
        abbr: 'EBITDA_{T0+5}',
        keywords: 'ebitda terminal earnings revenue opex carbon tax year T0 plus 5 horizon',
        definition: 'The conglomerate\'s normalised earnings before interest, taxes, depreciation, and amortisation projected at the end of the 5-year strategic cycle (starting year + 5). It synthesises ten rounds of revenue growth, OPEX evolution, and carbon liability into a single profitability figure used to anchor the exit valuation.',
        logic: 'Calculated in round_logic.py ? _post_r10_grand_finale(). Carbon tonnage is computed as carbon_intensity × revenue_base / 1,000,000 per BU (AUDIT-027 formula). A carbon tax of $250/tonne (god-mode overridable) is then deducted. The result feeds directly into the terminal value equation as the base earnings figure.',
        formula: `$$\\text{EBITDA}_{T_0+5} = \\sum_{i=1}^{n}\\left(\\text{Revenue}_i - \\text{OPEX}_i\\right) - \\underbrace{\\left(\\sum_{i=1}^{n} \\frac{\\text{CarbonIntensity}_i \\times \\text{Revenue}_i}{10^6}\\right) \\times \\tau_C}_{\\text{Carbon Cost}}$$
$$\\text{where } \\tau_C = \\$250 \\text{ per tonne CO}_2\\text{-e (default)}$$`,
        significance: 'The carbon deduction creates a direct, non-linear feedback between environmental decisions (Rounds 3, 5, 7) and financial outcomes. A $1M carbon saving in EBITDA translates to up to ~$20M in terminal value under optimal M_R conditions. This teaches the exponential cost of climate procrastination.',
      },
      {
        id: 'ncd',
        name: 'Natural Capital Debt (NCD)',
        abbr: 'NCD',
        keywords: 'natural capital debt ncd interest rate compounding ecological tipping point',
        definition: 'A BU-level liability representing accumulated environmental degradation—water depletion, soil toxicity, biodiversity loss—that the biosphere has not yet invoiced. In the simulation, it accrues an interest rate that compounds every round, modelling ecological tipping points and escalating remediation costs.',
        logic: 'Computed in engine.py ? calc_natural_capital_interest(). The interest rate rises linearly with NCD size, creating exponential compounding for high-debt BUs. NCD is floored at 0 (VULN-004) and capped at 1,000,000 (VULN-007). Reductions available via R3-B (Green Bond, -15), R7-A (Circular Redesign, -12), and R8-C (Desalination, -30).',
        formula: `$$r_{\\text{NCD}} = r_{\\text{base}} + \\left(\\text{NCD} \\times 0.0005\\right)$$
$$\\text{NCD}_{t+1} = \\text{NCD}_t \\times \\left(1 + r_{\\text{NCD}}\\right), \\quad r_{\\text{base}} = 0.05$$`,
        significance: 'NCD operationalises the concept of planetary boundaries as financial risk. A Pharma BU with NCD = 5,200 faces an effective interest rate of 2.65, meaning its debt will increase 3.65× in one round. Teams often ignore NCD in early rounds; the simulation is designed to punish that myopia with runaway compounding that becomes impossible to remediate by Round 8.',
      },
      {
        id: 'tv',
        name: 'Terminal Value',
        abbr: 'TV',
        keywords: 'terminal value exit multiple 12x M_R regenerative valuation enterprise',
        definition: 'The simulated market capitalisation of the Muressons Group at the end of the 5-year strategic cycle (Year T0+5). It represents what a sophisticated institutional investor—integrating ESG risk premia, carbon liability, and social licence—would pay to acquire the conglomerate at the simulation\'s conclusion.',
        logic: 'Anchored by a 12× exit EBITDA multiple (industry-standard manufacturing/tech composite), then scaled by the Regenerative Multiple M_R. The resulting archetype profiles range from "Stranded Relic" (M_R < 0.8) to "Regenerative Titan" (M_R = 1.8), with up to a $273M terminal value gap between worst and best strategies.',
        formula: `$$\\text{TV} = \\text{EBITDA}_{T_0+5} \\times \\underbrace{12}_{\\text{Exit Multiple}} \\times M_R$$`,
        significance: 'The M_R modifier—which can range from 0.6 to 1.65—means that the how of running the business matters as much as the what. A 0.6-point difference in M_R translates to roughly $91M in enterprise value. This teaches C-suite participants that governance and social licence are accretive to valuation, not merely compliance costs.',
      },
      {
        id: 'synergy',
        name: 'OPEX Synergy Reduction',
        abbr: 'Synergy Engine',
        keywords: 'synergy opex reduction investment ratio multiplier efficiency cross-BU',
        definition: 'Models the effect of cross-BU investment on shared cost structures. An investment ratio applied against the global Synergy Multiplier determines the percentage of OPEX that can be eliminated through integrated technology, shared services, or circular material flows.',
        logic: 'Computed in engine.py ? calc_synergy_opex(). Investment Ratio (CAPEX/Revenue) is clamped to [0, 1.0] (VULN-002). A round-7 Waste-to-Energy decision (Option C) boosts the Synergy Multiplier by +0.30 (+0.10 more for early_decarboniser teams), making future CAPEX dramatically more efficient and unlocking Round 10\'s "Resist & Integrate" option.',
        formula: `$$\\text{OPEX}_{t+1} = \\text{OPEX}_t \\times \\left(1 - \\text{InvRatio} \\times \\phi_{\\text{syn}}\\right)$$
$$\\text{InvRatio} = \\frac{\\text{CAPEX}_i}{\\text{Revenue}_i} \\in [0,\\;1.0], \\quad \\phi_{\\text{syn}} \\in [1.0,\\; 1.35]$$`,
        significance: 'Synergy is the simulation\'s analogue to dynamic capabilities theory: the ability to reconfigure internal competencies faster than competitors. A synergy multiplier of 1.35 vs 1.0 makes each reinvestment dollar 35% more productive—a structural advantage that cannot be replicated by late-stage spending.',
      },
      {
        id: 'gcod',
        name: 'Green Cost of Debt',
        abbr: 'GCoD',
        keywords: 'green cost of debt ncd environmental liability interest green bond financed',
        definition: 'A composite KPI that approximates the annualised financial burden attributable to ecological liabilities across all business units. It is reported in the Round 10 TBL-BSC Grid as a percentage figure expressing how much of the firm\'s capital is being consumed by environmental remediation obligations.',
        logic: 'Computed in round_logic.py ? _post_r10_grand_finale(). The 5% coefficient represents a regulatory premium applied to unresolved natural capital liabilities, modelling green bond spreads observed in OECD sustainable finance markets.',
        formula: `$$\\text{GCoD} = \\left(\\sum_{i=1}^{n} \\text{NCD}_i\\right) \\times 0.05$$`,
        significance: 'A CFO using a Green Cost of Debt lens can identify which BU carries the highest environmental drag on the P&L. The metric directly models the ECB\'s Green Bond Standard premium and TCFD\'s financial materiality of nature-related risks. Teams that allow NCD to compound face a higher GCoD, representing higher borrowing costs from ESG-integrated lenders.',
      },
      {
        id: 'dividend',
        name: 'Dividend Ratchet & Board Pressure',
        abbr: 'Div Ratchet',
        keywords: 'dividend ratchet board pressure distribution cut reputation investor expectations',
        definition: 'A governance mechanism that penalises teams who cut dividends by more than 20% relative to the previous round. Cutting dividends triggers a -5 Group Reputation hit, modelling real-world investor expectations for distribution consistency and the board accountability pressure that accompanies it.',
        logic: 'Evaluated in engine.py ? calc_dividend_ratchet(). Compares current_dividends against previous_round_dividends × 0.80. If below threshold, applies reputation penalty. Dividends are clamped to available treasury (VULN-001). This creates a strategic tension: reducing dividends frees cash for CAPEX but damages stakeholder confidence.',
        formula: `$$\\text{If Dividends}_t < 0.80 \\times \\text{Dividends}_{t-1}: \\quad \\text{Rep}_{t+1} = \\text{Rep}_t - 5$$`,
        significance: 'Ref: Lintner, J. (1956). "Distribution of Incomes of Corporations Among Dividends, Retained Earnings, and Taxes." American Economic Review, 46(2), 97-113. The Dividend Ratchet operationalises Lintner\'s partial adjustment model: managers smooth dividends because cuts signal negative private information to markets.',
      },
      {
        id: 'implementation',
        name: 'Implementation Lag & J-Curve Returns',
        abbr: 'Impl. Lag',
        keywords: 'implementation lag deferred returns J-curve CAPEX delay investment timing',
        definition: 'Infrastructure investments whose financial benefits are not immediately realised but mature over 1-2 subsequent rounds. Investments exceeding 10% of BU revenue are automatically deferred by one round, modelling the real-world construction/gestation period between capital commitment and operational benefit.',
        logic: 'Applied in engine.py ? calc_synergy_opex(). If investment_ratio > 0.10, the effective_ratio for the current round is set to 0 (benefit deferred). The pending benefit is stored in global_round_states.pending_capex_projects with rounds_remaining = 1. R5-A Hard Engineering uses a 2-round delay for resilience protection.',
        formula: `$$\\text{If InvRatio}_i > 0.10: \\quad \\text{Effective}_{t} = 0, \\quad \\text{Effective}_{t+1} = \\sqrt{\\text{InvRatio}} \\times 0.7$$
$$\\text{Pending Project: }\\{\\tau_{\\text{rem}} = 1, \\; \\text{effect}: \\Delta\\text{OPEX}\\}$$`,
        significance: 'Ref: Dixit, A.K. & Pindyck, R.S. (1994). "Investment under Uncertainty." Princeton University Press. The implementation lag teaches that real options have gestation periods—teams who spend heavily in R1 expecting immediate OPEX savings are forced to absorb a full round of costs before benefits materialise, creating the classic J-curve payoff profile.',
      },
      {
        id: 'caroic',
        name: 'Carbon-Adjusted Return on Invested Capital (CAROIC)',
        abbr: 'CAROIC',
        keywords: 'caroic carbon adjusted return invested capital roic nopat shadow carbon price tax rate carbon efficiency',
        definition: 'A carbon-aware extension of traditional ROIC that inflates the effective capital base by a shadow carbon cost, penalising carbon-intensive firms and rewarding decarbonisation. CAROIC makes it impossible to achieve a high return rating while carrying heavy carbon exposure—bridging the gap between financial and environmental KPIs.',
        logic: 'Computed in engine.py → calc_caroic(). Called every tick after EBITDA and tCO₂e are calculated. Uses corporate treasury as invested capital proxy (floored at $0 for insolvent firms). Shadow carbon price defaults to $250/ton (aligned with R10 carbon_tax_per_ton, god-mode overridable). Tax rate defaults to 25%. Grade scale: A+ (≥25%), A (≥15%), B (≥10%), C (≥5%), D (≥0%), F (<0%). Results displayed on both player Financial tab and facilitator Session Health Monitor.',
        formula: `$$\\text{CAROIC} = \\frac{\\text{EBITDA} \\times (1 - \\tau)}{\\text{Invested Capital} + \\text{Carbon Tonnage} \\times P_{\\text{shadow}}}$$
$$\\text{where } \\tau = 0.25, \\quad P_{\\text{shadow}} = \\$250/\\text{tCO}_2\\text{e}$$
$$\\text{NOPAT} = \\text{EBITDA} \\times (1 - \\tau), \\quad \\text{Carbon Tonnage} = \\sum_{i=1}^{n} \\frac{\\text{CI}_i \\times \\text{Rev}_i}{10^6}$$`,
        significance: 'Traditional ROIC rewards pure financial efficiency without regard for environmental externalities. CAROIC introduces a shadow carbon cost that inflates the effective capital base of carbon-intensive firms, revealing the true cost of carbon dependence. Example: EBITDA=$33M, Treasury=$50M, Carbon=2,850t → NOPAT=$24.75M, Carbon Charge=$712K, Adj. Capital=$50.7M → CAROIC=48.8% (A+). If carbon rises to 12,000t → CAROIC=46.7%, a 2.1ppt compression from carbon drag alone.',
      },

    ],
  },
  {
    id: 'es',
    number: '02',
    tag: 'Cluster II',
    title: 'Sustainability & ESG',
    desc: 'The ecological, social, and governance variables that drive non-financial risk and unlock—or destroy—the firm\'s Regenerative Multiple.',
    accentColor: '#6dbf87',
    terms: [
      {
        id: 'rep',
        name: 'Group Reputation & Contagion Engine',
        abbr: 'Rep / Contagion',
        keywords: 'group reputation contagion crisis severity BU cascade electronics',
        definition: 'A composite [0–100] score representing how stakeholders—media, regulators, investors, NGOs—perceive the Muressons Group. The Contagion Engine is the mechanism by which a single BU\'s reputational damage cascades to the entire group score.',
        logic: 'Computed in engine.py ? calc_contagion(). Crisis severity is set by pre_tick (R4 = 40 base; doubled to 80 if electronics_blindspot flag is active from an R1-A/C choice). Clamped to [0, 100]. A drop below 65 triggers the Talent Brain-Drain penalty on the Software BU.',
        formula: `$$\\text{GroupRep}_{t+1} = \\left(\\frac{1}{n}\\sum_{i=1}^{n}\\text{Rep}_i\\right) - \\left(\\sigma_{\\text{crisis}} \\times 0.4\\right)$$
$$\\text{R4: }\\sigma_{\\text{crisis}} = \\begin{cases} 80 & \\text{if electronics\\_blindspot active} \\\\ 40 & \\text{otherwise}\\end{cases}$$`,
        significance: 'The contagion formula is the simulation\'s most direct model of systemic reputational risk. A single BU\'s scandal (Electronics, R4) can drag the entire group score below critical thresholds, triggering talent drain, strike risk, and the instability discount on terminal value. The R1 forensic audit decision is the only meaningful hedge.',
      },
      {
        id: 'slo',
        name: 'Social Licence to Operate (SLO)',
        abbr: 'SLO',
        keywords: 'social license SLO operate strike probability stakeholder community worker',
        definition: 'A BU-level score [0–100] that quantifies community and worker acceptance of the BU\'s operations. Derived from political economy theory, it represents the ongoing legitimacy granted by host communities—distinct from legal permission—earned through inclusive stakeholder engagement.',
        logic: 'Directly feeds the Strike Probability Engine in engine.py ? calc_strike_probability(). The instability discount in M_R (-0.40) is triggered when the average SLO falls below 75. R9-A (Immediate Closure) drops SLO by 20 and creates a 75% strike probability if already below 50.',
        formula: `$$P_{\\text{strike}} = \\frac{\\text{GovRisk}_i}{100} + \\left(1 - \\frac{\\text{SLO}_i}{100}\\right) \\times 0.4, \\quad P_{\\text{strike}} \\in [0,\\;1]$$
$$\\text{Instability Discount: }\\Delta M_R = -0.40 \\text{ if }\\overline{\\text{SLO}} < 75$$`,
        significance: 'A CHRO should note that an SLO below 50 creates a potential R9 strike that eliminates an entire round\'s revenue from the treasury. The $12M Managed Transition investment (R9-B) compared to the potential $75M+ revenue loss from a strike is the clearest ROI calculation in the entire simulation.',
      },
      {
        id: 'dm',
        name: 'Double Materiality Framework',
        abbr: 'CSRD / DM',
        keywords: 'double materiality CSRD financial impact societal quadrant CFO gate',
        definition: 'Requires players to classify ESG issues on two axes: Financial Materiality (does it affect the firm\'s value?) and Impact Materiality (does the firm affect society/environment?). An issue is doubly material if it scores high on both axes—these are the mandatory first-priority investments per CSRD Article 19a.',
        logic: 'Validated in round_logic.py ? _pre_r2_materiality_gate(). If CAPEX is allocated to a non-Quadrant 1 issue without a CFO Override, the transaction is rejected. The CFO Override bypass reduces Group Reputation by -5. Six issues sit in Quadrant 1: Water Scarcity, E-Waste, Tier-3 Labour, AI Bias, Scope 3 Carbon, and Plastic Packaging.',
        formula: `$$\\text{Quadrant 1: }\\text{FinancialImpact} = \\text{High},\\;\\text{SocietalImpact} = \\text{High}$$
$$\\text{CFO Override Penalty: }\\text{Rep}_{t+1} = \\text{Rep}_t - 5$$`,
        significance: 'The CSRD mandates double materiality assessments for ~50,000 EU-regulated companies from 2025. The simulation teaches executives to resist the intuitive tendency to prioritise visible ESG issues (LED bulbs, volunteering) over material ones (water scarcity, scope 3). Misallocated capital in R2 is permanently unavailable for downstream risk mitigation.',
      },
      {
        id: 'carbon',
        name: 'Carbon Intensity & Scope 3 Emissions',
        abbr: 'Carbon / Scope 3',
        keywords: 'carbon intensity scope 3 emissions supply chain decarbonisation tax SBTi',
        definition: 'Carbon Intensity is a BU-level metric (tCO2-e per $M revenue) representing embedded emissions normalised to economic output. Scope 3 includes all indirect emissions in the value chain—the simulation specifies that Muressons\' supply chain footprint is 4× its direct operational emissions.',
        logic: 'Modified by R3 decisions: Option A (Rapid Supplier Switch) reduces intensity by -15; Option B (Green Bond) reduces by -8 and drops NCD by -15. Carbon tonnage is calculated at R10 as the revenue-scaled product, then taxed at $250/tonne. The UN SDG pathway adds a Carbon Retribution Multiplier (up to ×3) applied to R5 climate damage.',
        formula: `$$\\text{CarbonTonnage}_{\\Sigma} = \\sum_{i=1}^{n} \\frac{\\text{CarbonIntensity}_i \\times \\text{Revenue}_i}{10^6}$$
$$\\text{R5 Retribution: }\\text{ClimateDamage}^* = \\text{ClimateDamage} \\times \\lambda,\\;\\lambda \\in [1,\\;3]$$`,
        significance: 'Deferring Scope 3 reductions to R7 or later saves short-term cash but allows carbon intensity to compound across three BU revenue bases. By R10, a modest 5-unit intensity differential translates to hundreds of thousands in additional carbon cost—then amplified by the 12× exit multiple.',
      },
      {
        id: 'talent',
        name: 'Talent Brain-Drain Penalty',
        abbr: 'Brain-Drain',
        keywords: 'talent brain drain software opex penalty reputation human capital burnout',
        definition: 'An OPEX inflation mechanism specific to the Software (or Telehealth) BU that activates when Group Reputation falls below 65. It models the labour market reality that knowledge workers exit firms with poor ESG or social reputations faster than firms can replace them, inflating recruitment and retention costs.',
        logic: 'Computed in engine.py ? calc_talent_braindrain(). The penalty multiplier is applied as a direct inflation of the Software BU\'s opex_base. In the worked example: Group Rep = 54.59 ? 15.6% OPEX inflation. The penalty persists until reputation recovers above 65.',
        formula: `$$\\text{Penalty}_{\\text{talent}} = 1 + \\max\\!\\left(0,\\; \\frac{65 - \\text{GroupRep}}{100}\\right) \\times 1.5$$
$$\\text{OPEX}_{\\text{software},\\;t+1} = \\text{OPEX}_{\\text{software},\\;t} \\times \\text{Penalty}_{\\text{talent}}$$`,
        significance: 'A 15% OPEX inflation on an $8M base is a $1.2M annual drag—material enough to erode the entire advantage of a well-timed CAPEX investment. This models the ESG-driven employee exodus phenomenon where >70% of tech workers factor company values into job choices.',
      },
      {
        id: 'entropy',
        name: 'Natural Decay (Entropy Engine)',
        abbr: 'Entropy',
        keywords: 'natural decay entropy zero investment reputation SLO degradation neglect',
        definition: 'Models the thermodynamic reality that stakeholder goodwill and socio-ecological systems erode over time without active investment. A BU whose own investment ratio sits below 15% of the CSF pool with under $100k of CapEx loses 4% of its reputation score and 4% of its social licence score that round; at 15% it holds, at 20% licence grows +1, at 30% (or $3M of CapEx) it grows +3 to +10—the "standing still is falling behind" principle.',
        logic: 'Applied in engine.py → apply_natural_decay(), on each BU\'s OWN investment ratio (WP-21, 2026-09-05 — it used to read the team average). Below the 15% tier with under $100k of CapEx, both reputation and SLO are multiplied by 0.96. Over 5 rounds of neglect, a BU starting at Rep = 80 decays to 65.3—below the instability discount threshold if SLO follows the same trajectory.',
        formula: `$$\\text{If InvRatio}_i < 0.15 \\text{ and CAPEX}_i < \\$100k:\\quad \\text{Rep}_{t+1} = \\text{Rep}_t \\times 0.96,\\quad \\text{SLO}_{t+1} = \\text{SLO}_t \\times 0.96$$
$$\\text{Compound: }\\text{Rep}_{t+k} = \\text{Rep}_t \\times (0.96)^k$$`,
        significance: 'Entropy teaches portfolio management discipline. Teams instinctively concentrate investment in their highest-revenue BUs, leaving lower-margin units to decay. A BU neglected for 5 rounds loses ~18% of its scores, which can cross the SLO threshold (75) and trigger the M_R instability discount that devalues the entire group.',
      },
      {
        id: 'water',
        name: 'Water Dependency Index',
        abbr: 'Water Dep',
        keywords: 'water dependency blue stress watershed depletion scarcity physical risk TCFD',
        definition: 'A BU-level [0–1] score representing the proportion of a BU\'s operational continuity that is contingent on stable freshwater access. A score of 0.8 (Electronics baseline) means 80% of that BU\'s operations would be impaired under water stress scenarios, creating a stranded asset risk analogous to TCFD\'s physical climate risk exposures.',
        logic: 'Modified exclusively in Round 8 (Blue Stress). Option A (Water Efficiency, -20 to all BUs), Option C (Desalination, -40 delayed by 2 rounds via pending CAPEX project). High water dependency increases exposure to R8\'s watershed depletion crisis, which applies social licence penalties and blocks the M_R resilience bonus if Option B is chosen.',
        formula: `$$\\text{WaterDep}_{t+1} = \\max\\left(0,\\; \\text{WaterDep}_t + \\Delta_{\\text{WD}}\\right)$$
$$\\Delta_{\\text{WD}} = \\begin{cases} -0.20 & \\text{R8 Option A (immediate)} \\\\ -0.40 & \\text{R8 Option C (delayed, }\\tau = 2\\text{ rounds)} \\end{cases}$$`,
        significance: 'Water scarcity is projected to affect 40% of global manufacturing by 2030 (WRI). A COO who ignores Water Dependency faces a Round 8 scenario where their highest-dependency BUs lose SLO scores that cascade into the M_R instability discount, despite having no financial liability visible on the P&L.',
      },
      {
        id: 'burnout',
        name: 'Staff Burnout & Workforce Wellbeing',
        abbr: 'Burnout',
        keywords: 'staff burnout wellbeing workforce WHO ICD-11 hr opex penalty fatigue exhaustion',
        definition: 'A global workforce metric [0–100] representing cumulative occupational exhaustion across all business units. Recognised by WHO in ICD-11 (2019) as an occupational phenomenon. In the simulation, burnout compounds OPEX penalties and blocks the +0.05 M_R Wellbeing Champion bonus if above 20 at R10.',
        logic: 'Modified by HR investment decisions in the Strategic Pillars paradigm. High HR: -10, Medium: -4, None: +3 drift per round. OPEX penalty activates above 20: penalty = ((burnout-20)²) × 0.000028. Critical threshold at 70 triggers additional governance risk increases.',
        formula: `$$\\text{Burnout}_{t+1} = \\text{Burnout}_t + \\Delta_{\\text{HR}} + 3_{\\text{drift}}$$
$$\\text{OPEX Penalty} = \\left(\\max(0, \\text{Burnout} - 20)\\right)^2 \\times 0.000028$$
$$\\text{Wellbeing Bonus: }+0.05\\;M_R \\text{ iff }\\overline{\\text{Burnout}} < 20 \\text{ at R10}$$`,
        significance: 'Ref: WHO (2019). ICD-11 Burn-out Classification (QD85). Maslach, C. & Leiter, M. (2016). "Understanding Burnout." World Psychiatry, 15(2). The simulation models burnout as an organisational externality: individual-level exhaustion compounds into enterprise-wide productivity loss, creating a hidden OPEX drag that is invisible on standard P&L reports until it reaches critical mass.',
      },
      {
        id: 'readiness',
        name: 'Workforce Readiness Index',
        abbr: 'WRI',
        keywords: 'workforce readiness competence training learning organisational capacity HR human capital',
        definition: 'A global competence score [0–100, starting at 50] that measures the organisation\'s collective ability to execute strategic initiatives. Low readiness (<40) reduces the effectiveness of all pillar decisions by 20%. High readiness (=75) earns a +0.10 M_R bonus at terminal valuation.',
        logic: 'Modified by HR investment in Strategic Pillars. High HR: +8, Medium: +4, None: -5 per round. Feeds into pillar_effectiveness_multiplier = 0.80 if readiness < 40, else 1.0. The readiness score is a proxy for organisational learning capacity (Senge, 1990).',
        formula: `$$\\text{WRI}_{t+1} = \\text{WRI}_t + \\Delta_{\\text{HR}}, \\quad \\Delta \\in \\{-5, +4, +8\\}$$
$$\\text{Pillar Effectiveness} = \\begin{cases} 0.80 & \\text{WRI} < 40 \\\\ 1.00 & \\text{otherwise} \\end{cases}$$
$$\\text{M_R Bonus: }+0.10 \\text{ iff WRI} \\geq 75 \\text{ at R10}$$`,
        significance: 'Ref: Senge, P. (1990). "The Fifth Discipline." Currency Doubleday. Becker, G. (1964). "Human Capital." NBER. The workforce readiness metric operationalises the resource-based view of human capital: organisations that systematically underinvest in talent development erode their capacity to execute even well-designed strategies.',
      },
      {
        id: 'greenwash',
        name: 'Greenwashing Detection Engine',
        abbr: 'Greenwash',
        keywords: 'greenwashing ESG misrepresentation social license penalty rhetoric investment ratio ESMA',
        definition: 'An automated detection engine that identifies discrepancies between stated ESG commitments and actual investment behaviour. Every option carries a green-claim level (full / moderate / none). A full claim backed by less than 15% of the CSF pool this round (the team\'s total allocation as a share of the fund) — or a moderate claim below ≈10% — triggers a 15-point (moderate: 7.5-point) SLO penalty across ALL business units, unless total CapEx is at least $3M. A scandal is also remembered as a betrayal by the stakeholder agents.',
        logic: 'Computed in engine.py → calc_greenwashing_risk(). Reads the chosen option\'s green_claim (full 15% bar, moderate ≈10% bar, none → not checked), the team\'s pre-austerity share of the CSF pool (sum of the BU ratios) and the $3M total-CapEx absolute escape. The penalty is applied to social_license_score for every BU simultaneously, modelling the reputational cascade from a public greenwashing scandal.',
        formula: `$$\\text{If claim = full AND }\\sum_{i=1}^{n} \\text{InvRatio}_i < 0.15 \\text{ (moderate: } < 0.10\\text{) AND total CAPEX} < \\$3M: \\quad \\forall i:\; \\text{SLO}_i \\mathrel{-}= 15 \\text{ (moderate: } 7.5)$$`,
        significance: 'Ref: ESMA (2023). Guidelines on Funds\' Names Using ESG or Sustainability-Related Terms. Lyon, T. & Montgomery, A. (2015). "The Means and End of Greenwash." Organization & Environment, 28(2). The engine teaches that ESG commitments without capital backing create regulatory and reputational exposure that compounds over time.',
      },

    ],
  },
  {
    id: 'sp',
    number: '03',
    tag: 'Cluster III',
    title: 'Strategic Positioning',
    desc: 'The competitive architecture variables—VRIO, flag dependencies, archetypes, and the Regenerative Multiple—that determine how strategic choices compound into long-run advantages.',
    accentColor: '#bf7c6d',
    terms: [
      {
        id: 'vrio',
        name: 'VRIO Competitive Advantage & Decay',
        abbr: 'VRIO',
        keywords: 'VRIO competitive advantage imitation decay synergy multiplier resource-based view dynamic capabilities',
        definition: 'The VRIO framework (Value, Rarity, Inimitability, Organisation) is implemented as a continuous decay function on the Synergy Multiplier—the simulation\'s proxy for accumulated competitive advantage. Decay models real-world erosion of proprietary positions through competitor imitation or regulatory commoditisation.',
        logic: 'Computed in engine.py ? calc_vrio_decay(). The imitation decay rate defaults to 5% per round. The resulting Synergy Multiplier is stored in global_round_states.synergy_multiplier. The R7-C Waste-to-Energy choice adds +0.30 (+0.10 more for early_decarboniser teams), which must then survive subsequent decay—making timing critical for R10 terminal valuation.',
        formula: `$$\\phi_{\\text{syn},\\;t+1} = \\phi_{\\text{syn},\\;t} \\times \\left(1 - \\delta_{\\text{imitation}}\\right), \\quad \\delta_{\\text{imitation}} = 0.05$$
$$\\text{R7-C Boost: }\\phi_{\\text{syn}} \\mathrel{+}= 0.30 \\quad | \\quad \\text{R10 Gate: }\\phi_{\\text{syn}} \\times 100 > 80$$`,
        significance: 'VRIO decay ensures that competitive advantage is not a stock but a flow that must be continuously replenished. A Chief Strategy Officer who "wins" early rounds must continue to defend that position through subsequent CAPEX, or watch the multiplier erode below the R10 Option A gate (threshold 80). This directly models Teece\'s dynamic capabilities.',
      },
      {
        id: 'mr',
        name: 'Regenerative Multiple (M_R)',
        abbr: 'M_R',
        keywords: 'regenerative multiple MR truth premium resilience bonus synergy instability discount archetype',
        definition: 'The simulation\'s most important single number: a risk-adjusted valuation modifier that reflects what ESG-informed institutional investors apply to EBITDA when pricing a company\'s exit multiple. It rewards regenerative strategies and penalises extractive or high-instability management.',
        logic: 'Computed by terminal_valuation.calculate_mr — the single arbiter — from the flags and KPIs the team finishes with. Additive components (ramped, not cliffs): +0.10 Materiality Governance (R2 matrix; +0.05 partial), +0.15 Synergy Strategic Premium (R7-C synergy_unlock AND synergy multiplier ≥ 0.80 — the OPEX saving itself is already in EBITDA), +0.20 Resilience Champion (no R5-C/R8-B bailouts), +0.15 Truth Premium (R6-B ethical_ai_overhaul), +0.18 Community Champion and +0.12 Just Transition (scaled by HR-investment rounds), +0.10 Workforce Excellence (readiness), +0.05 Wellbeing (low burnout); −0.20 Planet Expendable; the BRSR ESG Alpha Dividend where that track ran; and −0.40 × shortfall Instability Discount (average SLO below 75, ramped). Ending-pathway bonuses add on top. Clamped to [0.0, 2.05]; the default-pathway maximum is 1.93 (2.02 with Just-Transition scaling).',
        formula: `$$M_R = 1.0 + \\Delta_{\\text{materiality}} + \\Delta_{\\text{synergy}} + \\Delta_{\\text{resilience}} + \\Delta_{\\text{truth}} + \\Delta_{\\text{community}} + \\Delta_{\\text{just\\_transition}} + \\Delta_{\\text{workforce}} + \\Delta_{\\text{wellbeing}} - \\Delta_{\\text{planet}} - 0.40\\cdot\\frac{\\max(0,\\,75-\\overline{\\text{SLO}})}{75}$$
$$M_R \\in [0.0,\\;2.05],\\quad M_R^{\\max}_{\\text{default pathway}} = 1.93$$`,
        significance: 'Each M_R component maps to a real-world investor framework: Synergy→Circular Economy premiums, Resilience→TCFD risk reduction, Truth Premium→ESG governance index premium, Instability→activist investor impairment pricing (Danone 2021, Exxon 2021). Terminal value = max(0, EBITDA) + Green Fund, × the WACC-linked exit multiple, × M_R, × M_SDG — so M_R is the largest single lever a team controls at exit.',
      },
      {
        id: 'flags',
        name: 'Flag Dependency Architecture',
        abbr: 'Flags',
        keywords: 'flag dependency electronics blindspot contagion cascade path dependence decision tree',
        definition: 'Persistent boolean state variables stored in global_round_states.active_event_flags that encode consequences of past decisions into future round engines. They represent path dependence in strategic management: early choices create structural asymmetries in the decision space of later rounds.',
        logic: 'Flags are set by _apply_option_flags() and read by _collect_all_flags(). Critical flags: electronics_blindspot (R1-A/C → doubles R4 crisis), insurance_only/electronics_water_priority (R5-C/R8-B → blocks M_R +0.20), ethical_ai_overhaul (R6-B → M_R +0.15), synergy_unlock (R7-C → M_R +0.15 when the synergy multiplier is still ≥ 0.80, and enables R10 Option A).',
        formula: `$$\\text{R1: A/C}\\xrightarrow{\\text{sets}}\\texttt{electronics\\_blindspot}\\xrightarrow{\\text{doubles}}\\sigma_{\\text{crisis,R4}} = 80$$
$$\\text{R6: B}\\xrightarrow{\\text{sets}}\\texttt{ethical\\_ai\\_overhaul}\\xrightarrow{\\text{unlocks}}\\Delta M_R^{\\text{truth}} = +0.15$$
$$\\text{R7: C}\\xrightarrow{\\text{sets}}\\texttt{synergy\\_unlock}\\xrightarrow{\\text{unlocks}}\\Delta M_R^{\\text{syn}} = +0.15 \\;\\&\\;\\text{R10 Option A}$$`,
        significance: 'Strategy is not a series of isolated decisions but an interconnected system. The flags create switching costs—teams who chose R1-A cannot undo the electronics blindspot by spending more in R2. Governance architecture (audit depth, AI ethics, circular economy commitments) must be embedded early, before crises make them purely reactive and costly.',
      },
      {
        id: 'archetypes',
        name: 'Terminal Strategy Archetypes',
        abbr: 'Profile',
        keywords: 'archetype regenerative titan stranded relic fragile giant safe haven profile classification',
        definition: 'Qualitative-quant profiles assigned to simulation teams at Round 10 based on their Regenerative Multiple. Each archetype represents a distinct strategic posture with real-world corporate analogues, providing a memorable and emotionally resonant synthesis of the team\'s ten-round performance.',
        logic: 'Assigned in round_logic.py ? _post_r10_grand_finale(). Custom archetypes from God Mode take priority. Thresholds are configured in round_configs.py\'s special rules for Round 10. Facilitators can define alternative archetypes with custom icons, gradient colours, and narrative descriptions.',
        formula: `$$\\text{Profile} = \\begin{cases} \\text{?? Regenerative Titan} & M_R \\geq 1.8 \\\\ \\text{?? De-risked Safe-Haven} & 1.2 \\leq M_R < 1.8 \\\\ \\text{?? Fragile Giant} & 0.8 \\leq M_R < 1.2 \\\\ \\text{?? Stranded Relic} & M_R < 0.8 \\end{cases}$$`,
        significance: 'The archetypes map to real-world 2024–2025 corporate categories. The "Stranded Relic" evokes BP or Volkswagen post-dieselgate. The "Regenerative Titan" evokes Ørsted (former oil company, now world\'s largest offshore wind developer). The archetypes make the abstract M_R number emotionally legible and create competitive debrief dynamics.',
      },
      {
        id: 'climate',
        name: 'Stochastic Physical Climate Event',
        abbr: 'R5 / Climate Risk',
        keywords: 'stochastic roll climate event cyclone dice damage resilience physical risk TCFD',
        definition: 'Models a Category-4 cyclone whose occurrence is probabilistically determined by a random draw against a fixed threshold. The base damage is $12M, modulated by the team\'s prior investment in resilience infrastructure—a direct analogue to TCFD\'s scenario analysis requirements for physical risk.',
        logic: 'Governed by round_logic.py ? _post_r5_climate(). A random roll ? ~ U[0,1] strikes if ? < 0.75. Resilience from previously completed pending CAPEX projects mitigates damage (Hard Engineering resilience is delayed 2 rounds and does NOT protect the current round). Choice of R5-C (Insurance Only) blocks the M_R +0.20 resilience bonus.',
        formula: `$$\\xi \\sim \\mathcal{U}[0,\\;1],\\quad \\text{Event strikes iff }\\xi < 0.75$$
$$\\text{ActualDamage} = D_{\\text{base}} \\times \\left(1 - \\rho_{\\text{res}}\\right) \\times \\lambda_{\\text{ret}}$$
$$\\rho_{\\text{res}} \\in \\{0.0,\\;0.60,\\;0.85\\},\\quad \\lambda_{\\text{ret}} \\in [1,\\;3]$$`,
        significance: 'The EV of Option C (Insurance Only) is -$2M + 0.75×(-$12M) = -$11M vs. Option B (Nature-Based): -$5M + 0.75×(-0.40×$12M) = -$8.6M. The hidden cost of R5-C is the forfeited M_R +0.20, worth $28.8M in terminal value at median EBITDA. Expected value calculation with tail-risk accounting is the CFO skill being tested here.',
      },
      {
        id: 'just',
        name: 'Just Transition & Strike Mechanics',
        abbr: 'Just Transition',
        keywords: 'just transition workforce strike factory closure R9 social license community',
        definition: 'Models the human cost of decarbonisation: the closure of three legacy factories requires redistribution of economic value to displaced workers and affected communities. Operationalises the ILO/UN definition of just transition—ensuring the shift to a sustainable economy does not leave workers and communities behind.',
        logic: 'Strike probability evaluated in round_logic.py ? _post_r9_just_transition(). If average SLO < 50, a random roll is compared to a 75% strike probability. A successful strike converts all BU revenue for the round into a treasury deduction (AUDIT-003 fix). The Regulatory Friction variable models compliance overhead from SLO impairment.',
        formula: `$$\\text{RegulatoryFriction} = \\frac{1}{\\max(1,\\;\\overline{\\text{SLO}})}$$
$$\\text{If }\\overline{\\text{SLO}} < 50:\\quad \\zeta \\sim \\mathcal{U}[0,1],\\quad \\text{Strike iff }\\zeta < 0.75$$
$$\\text{StrikeCost} = \\sum_{i=1}^{n} \\text{Revenue}_i \\text{ (deducted from treasury)}$$`,
        significance: 'The Community Fund (R9-C, -$20M) prevents the strike entirely and adds +0.18 SLO, securing the M_R stability bonus worth ~$28M. A board that has made consistently extractive choices discovers in R9 that their accumulated SLO deficit creates a catastrophic financial exposure that the "expensive" ethical path would have prevented at a fraction of the cost.',
      },
      {
        id: 'gtf',
        name: 'Green Transition Fund (GTF)',
        abbr: 'GTF',
        keywords: 'green transition fund ring-fenced capital sustainability budget green bond ICMA',
        definition: 'A ring-fenced capital reserve established by specific early-round decisions, analogous to a corporate green bond issuance. It is drawn down first before the corporate treasury is tapped for sustainable transition costs in Rounds 7, 8, and 9—providing a capital allocation buffer that rewards early strategic commitment to sustainability.',
        logic: 'Managed in round_logic.py ? _post_r7_circularity() and _post_r8_blue_stress(). The fund acts as a priority spending pool: the engine first checks if green_transition_fund = cost, depletes it, and only draws from corporate treasury for any remainder. An exhausted fund leaves the full cost exposed on the treasury.',
        formula: `$$\\text{NetTreasuryCost} = \\max\\!\\left(0,\\; \\text{Cost} - \\text{GTF}_t\\right)$$
$$\\text{GTF}_{t+1} = \\max\\!\\left(0,\\; \\text{GTF}_t - \\text{Cost}\\right)$$`,
        significance: 'Green bonds now represent over $500B annual issuance globally. A CFO who establishes a GTF early gains a structural advantage—transition costs in later rounds draw from the dedicated pool rather than competing with operational investments for treasury. It also signals to lenders that sustainability costs are provisioned, aligning with ICMA Green Bond Principles.',
      },
      {
        id: 'capex',
        name: 'Pending CAPEX Projects (Delayed Returns)',
        abbr: 'Delayed CAPEX',
        keywords: 'pending capex projects delayed returns deferred investment resilience education infrastructure J-curve',
        definition: 'Infrastructure investments whose benefits are not immediately realised but mature over subsequent rounds. This mechanism models real-world capital project timelines: coastal resilience infrastructure, water desalination plants, and education programmes all require construction/gestation periods before delivering operational benefits.',
        logic: 'Stored as a list in global_round_states.pending_capex_projects. Each project has a rounds_remaining counter, decremented each tick. When it reaches 0, the project\'s effect (resilience_boost, ncd_drop, education multiplier) is applied to BU states. R5-A (Hard Engineering) purchases resilience protection in Round 7, not Round 5.',
        formula: `$$\\text{Project: }\\{t_{\\text{complete}} = t_{\\text{decision}} + \\tau,\\;\\text{effect}: \\Delta X_{\\text{target}}\\}$$
$$\\text{Active iff }\\tau_{\\text{rem}} = 0:\\quad X_{\\text{BU}} \\mathrel{+}= \\Delta X,\\quad \\tau = 2\\text{ rounds (default)}$$`,
        significance: 'Delayed returns expose a critical gap in executive thinking: the tendency to demand immediate returns conflicts with the reality that resilience, education, and infrastructure investments have J-curve payoff profiles. Teams that choose Hard Engineering in R5 believing it protects them immediately discover the 2-round lag the hard way—a lesson that maps directly to infrastructure project management and regulatory capital planning.',
      },
      {
        id: 'circular',
        name: 'Circular Economy & Industrial Symbiosis',
        abbr: 'Circularity',
        keywords: 'circular economy waste to energy industrial symbiosis Ellen MacArthur Foundation lifecycle redesign',
        definition: 'An economic model that eliminates waste and pollution by circulating products and materials at their highest value. In R7, the Industrial Symbiosis pathway (Option C: Waste-to-Energy) provides a +0.15 M_R Strategic Premium (the OPEX saving itself flows through EBITDA) by converting one BU\'s waste stream into another\'s energy input.',
        logic: 'Triggered by R7-C decision, which sets the synergy_unlock flag and adds +0.30 to synergy_multiplier. The M_R Strategic Premium (+0.15, ramped) is evaluated at R10 and requires BOTH the synergy_unlock flag and a synergy multiplier still ≥ 0.80 — VRIO decay can erode an earned unlock. It is also the gate for the "Resist & Integrate" R10 option.',
        formula: `$$\\text{R7-C: }\\phi_{\\text{syn}} \\mathrel{+}= 0.30, \\quad \\text{Flag: synergy\\_unlock} = \\text{True}$$
$$\\text{M_R Component: }\\Delta M_R^{\\text{syn}} = +0.15 \\text{ iff synergy\\_unlock AND }\\phi_{\\text{syn}} \\ge 0.80\\;(\\text{ramped})$$`,
        significance: 'Ref: Ellen MacArthur Foundation (2013). "Towards the Circular Economy." McDonough, W. & Braungart, M. (2002). "Cradle to Cradle." The R7 decision is the simulation\'s most consequential single choice: the synergy boost (+0.30) compounds through VRIO decay, and the M_R premium (+0.15) is worth roughly 15% of terminal value on top of the OPEX savings already in EBITDA.',
      },
      {
        id: 'justtrans',
        name: 'Just Transition & ILO Framework',
        abbr: 'Just Trans.',
        keywords: 'just transition ILO Paris Agreement workforce displacement community fund managed closure',
        definition: 'Operationalises the ILO/UN definition of just transition—ensuring the shift to a sustainable economy does not leave workers and communities behind. R9 presents three pathways with fundamentally different financial and social outcomes, from immediate closure (strike risk) to community fund (M_R bonus).',
        logic: 'R9-A (Immediate Closure): SLO -20, strike probability engine activates. R9-B (Managed Transition, -$12M): SLO neutral, +0.12 M_R. R9-C (Community Fund, -$20M): SLO +0.18 M_R, strike prevented. Strike probability is evaluated via engine.py ? calc_strike_probability() using SLO and governance risk.',
        formula: `$$\\text{R9-A: }P_{\\text{strike}} = \\frac{\\text{GovRisk}}{100} + \\left(1 - \\frac{\\text{SLO}}{100}\\right) \\times 0.4$$
$$\\text{R9-C: }\\Delta M_R^{\\text{community}} = +0.18 \\times \\text{JT\\_scaling}$$
$$\\text{StrikeCost} = \\sum_{i=1}^{n} \\text{Revenue}_i \\quad (\\text{deducted from treasury})$$`,
        significance: 'Ref: ILO (2015). "Guidelines for a Just Transition." Paris Agreement, Article 4(1). Rosemberg, A. (2010). "Building a Just Transition." ITUC. The R9 calculation reveals that the Community Fund (-$20M) has a positive expected value vs. Immediate Closure when strike probability exceeds 40%—making the ethical choice also the financially rational one.',
      },
      {
        id: 'aiethics',
        name: 'AI Ethics & EU AI Act Compliance',
        abbr: 'AI Ethics',
        keywords: 'AI ethics algorithmic bias EU AI Act recruitment transparency ethical overhaul truth premium',
        definition: 'R6 presents the discovery of systematic algorithmic bias in the Software BU\'s recruitment AI, creating a regulatory and ethical crisis. The three options model the full spectrum of corporate responses to AI governance failures, from ethical overhaul to monetisation of biased systems.',
        logic: 'R6-B (Ethical AI Overhaul, -$8M): sets ethical_ai_overhaul flag ? +0.15 M_R Truth Premium. R6-C (Monetise Algorithm, +$3M): sets ai_monetised flag ? EU AI Act compliance costs from R7 onward (estimated -$2M/round). R6-A (Partial Fix, -$3M): middle ground, no M_R bonus.',
        formula: `$$\\text{R6-B: }\\Delta M_R^{\\text{truth}} = +0.15, \\quad \\text{TV Impact} \\approx +\\$54M$$
$$\\text{R6-C: }\\text{EU AI Act Cost} = -\\$2M/\\text{round from R7} \\quad (\\text{3 rounds} = -\\$6M)$$
$$\\text{Net R6-B vs R6-C: }\\$54M - \\$8M \\text{ vs } \\$3M - \\$6M = +\\$46M\\text{ vs }-\\$3M$$`,
        significance: 'Ref: EU AI Act (Regulation 2024/1689). Jobin, A. et al. (2019). "The Global Landscape of AI Ethics Guidelines." Nature Machine Intelligence, 1, 389-399. The Truth Premium teaches that ethical AI governance is not a cost centre but a value-accretive investment. The $8M overhaul generates $54M in terminal value—a 6.75× return.',
      },

    ],
  },
];

// --- Accent colors per cluster ----------------------------------------------
const CLUSTER_ACCENT = { fi: '#4ca8c9', es: '#6dbf87', sp: '#bf7c6d' };

// --- MathJax loader (idempotent) --------------------------------------------
function useMathJax() {
  const loaded = useRef(false);
  useEffect(() => {
    if (loaded.current || typeof window === 'undefined') return;
    loaded.current = true;
    if (window.MathJax?.typesetPromise) return;

    // Debounced auto-typesetter via MutationObserver
    let debounceTimer = null;
    const autoTypeset = () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        if (window.MathJax?.typesetPromise) {
          window.MathJax.typesetPromise().catch(() => {});
        }
      }, 300);
    };

    window.MathJax = {
      tex: {
        inlineMath: [['$','$']],
        displayMath: [['$$','$$']],
        processEscapes: false,
        packages: {'[+]': ['ams', 'noerrors']},
      },
      chtml: {
        mtextInheritFont: true,
      },
      options: { skipHtmlTags: ['script','noscript','style','textarea','pre','code'] },
      startup: {
        typeset: false,
        ready() {
          window.MathJax.startup.defaultReady();
          // Force MathJax to inherit page text color (fixes dark mode)
          const style = document.createElement('style');
          style.textContent = 'mjx-container, mjx-container * { color: inherit !important; }';
          document.head.appendChild(style);
          // Typeset everything on initial load
          window.MathJax.typesetPromise().catch(() => {});
          // Watch for new DOM content and auto-typeset
          const observer = new MutationObserver(autoTypeset);
          observer.observe(document.body, { childList: true, subtree: true, characterData: true });
        }
      },
    };
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js';
    s.async = true;
    document.head.appendChild(s);
  }, []);
}

function typesetEl(el) {
  if (!el) return;
  // Explicit typeset for a specific element — with retry for CDN loading
  const attempt = (retries) => {
    if (window.MathJax?.typesetPromise) {
      if (window.MathJax.typesetClear) window.MathJax.typesetClear([el]);
      window.MathJax.typesetPromise([el]).catch(() => {});
    } else if (retries > 0) {
      setTimeout(() => attempt(retries - 1), 400);
    }
  };
  // Wait for next frame to ensure DOM is painted
  requestAnimationFrame(() => setTimeout(() => attempt(25), 50));
}

// --- TermCard ---------------------------------------------------------------
function TermCard({ term, clusterAccent, searchQuery }) {
  const [open, setOpen] = useState(false);
  const bodyRef = useRef(null);

  useEffect(() => {
    if (open && bodyRef.current) typesetEl(bodyRef.current);
  }, [open]);

  // Auto-open if search query matches
  useEffect(() => {
    if (searchQuery && bodyRef.current) typesetEl(bodyRef.current);
  }, [searchQuery]);

  const cardStyle = {
    background: 'var(--bg-card)',
    border: '1px solid var(--border-subtle)',
    borderRadius: '10px',
    overflow: 'hidden',
    marginBottom: '16px',
    transition: 'border-color 0.2s, box-shadow 0.2s',
    fontFamily: 'var(--font-sans, Inter, system-ui, sans-serif)',
  };

  const headerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 20px',
    borderBottom: open ? '1px solid var(--border-subtle)' : '1px solid transparent',
    cursor: 'pointer',
    gap: '12px',
    background: open ? 'var(--bg-elevated, var(--bg-body))' : 'transparent',
    transition: 'background 0.2s',
  };

  const sectionLabelStyle = {
    fontSize: 'var(--type-caption)',
    fontWeight: 700,
    letterSpacing: '0.15em',
    textTransform: 'uppercase',
    color: clusterAccent,
    marginBottom: '6px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  };

  const dividerStyle = {
    flex: 1,
    height: '1px',
    background: clusterAccent,
    opacity: 0.25,
    display: 'inline-block',
  };

  const formulaBoxStyle = {
    background: 'var(--bg-elevated)',
    border: `1px solid ${clusterAccent}`,
    borderLeft: `3px solid ${clusterAccent}`,
    borderRadius: '6px',
    padding: '14px 18px',
    overflowX: 'auto',
    marginTop: '4px',
    color: 'var(--text-primary)',
  };

  const sigBoxStyle = {
    background: 'rgba(201,168,76,0.06)',
    border: '1px solid rgba(201,168,76,0.2)',
    borderRadius: '6px',
    padding: '12px 16px',
    marginTop: '4px',
  };

  return (
    <div style={cardStyle}>
      <div style={headerStyle} onClick={() => setOpen(v => !v)} role="button" aria-expanded={open}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)', lineHeight: 1.3 }}>
            {term.name}
          </div>
        </div>
        <span style={{
          fontSize: 'var(--type-caption)', fontFamily: 'var(--font-mono, monospace)',
          letterSpacing: '0.08em', color: 'var(--text-muted)',
          padding: '2px 8px', border: '1px solid var(--border-subtle)',
          borderRadius: '3px', whiteSpace: 'nowrap', flexShrink: 0,
        }}>{term.abbr}</span>
        <span style={{ color: open ? clusterAccent : 'var(--text-muted)', transition: 'transform 0.2s, color 0.2s', transform: open ? 'rotate(180deg)' : 'none', fontSize: '12px' }}>?</span>
      </div>

      {open && (
        <div ref={bodyRef} style={{ padding: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px 28px' }}>
          {/* Definition */}
          <div>
            <div style={sectionLabelStyle}>Formal Definition <span style={dividerStyle} /></div>
            <p style={{ fontSize: '0.85rem', lineHeight: 1.75, color: 'var(--text-primary)', margin: 0, fontWeight: 400 }}>{term.definition}</p>
          </div>

          {/* Operational Logic */}
          <div>
            <div style={sectionLabelStyle}>Operational Logic <span style={dividerStyle} /></div>
            <p style={{ fontSize: '0.85rem', lineHeight: 1.75, color: 'var(--text-primary)', margin: 0, fontWeight: 400 }}>{term.logic}</p>
          </div>

          {/* Formula — full width */}
          <div style={{ gridColumn: '1 / -1' }}>
            <div style={sectionLabelStyle}>Mathematical Formula <span style={dividerStyle} /></div>
            <div style={formulaBoxStyle}>
              {term.formula}
            </div>
          </div>

          {/* Strategic Significance — full width */}
          <div style={{ gridColumn: '1 / -1' }}>
            <div style={sectionLabelStyle}>Strategic Significance <span style={dividerStyle} /></div>
            <div style={sigBoxStyle}>
              <p style={{ fontSize: '0.85rem', lineHeight: 1.75, color: 'var(--text-secondary)', margin: 0 }}>{term.significance}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Main Component ----------------------------------------------------------
export default function TechnicalGlossary() {
  useMathJax();
  const [search, setSearch] = useState('');
  const [activeCluster, setActiveCluster] = useState('all');

  const q = search.trim().toLowerCase();

  const filteredClusters = useMemo(() => {
    return CLUSTERS
      .filter(c => activeCluster === 'all' || c.id === activeCluster)
      .map(c => ({
        ...c,
        terms: q
          ? c.terms.filter(t =>
              t.name.toLowerCase().includes(q) ||
              t.keywords.toLowerCase().includes(q) ||
              t.definition.toLowerCase().includes(q) ||
              t.significance.toLowerCase().includes(q)
            )
          : c.terms,
      }))
      .filter(c => c.terms.length > 0);
  }, [search, activeCluster]);

  const totalVisible = filteredClusters.reduce((s, c) => s + c.terms.length, 0);

  return (
    <div style={{ fontFamily: 'var(--font-sans, Inter, system-ui, sans-serif)', maxWidth: '1100px', margin: '0 auto', padding: '0 0 60px', color: 'var(--text-primary)' }}>

      {/* -- Header -- */}
      <div style={{ marginBottom: '28px', paddingBottom: '20px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ fontSize: '1.4rem' }}>??</span>
              <h2 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                Technical Glossary
              </h2>
              <span style={{
                fontSize: 'var(--type-caption)', fontWeight: 700, letterSpacing: '0.12em',
                textTransform: 'uppercase', padding: '3px 8px', borderRadius: '4px',
                background: 'linear-gradient(135deg, #c9a84c22, #c9a84c11)',
                border: '1px solid #c9a84c44', color: '#c9a84c',
              }}>30 Terms · 3 Clusters</span>
            </div>
            <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-muted)', maxWidth: '600px', lineHeight: 1.6 }}>
              Senior-level reference for every quantitative variable, formula, and strategic lever in the Muressons simulation engine.
              All equations verified against <code style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono,monospace)' }}>engine.py</code> and <code style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono,monospace)' }}>round_logic.py</code>.
            </p>
          </div>

          {/* Search */}
          <div style={{ position: 'relative', minWidth: '260px' }}>
            <span style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', fontSize: '14px', color: 'var(--text-muted)', pointerEvents: 'none' }}>??</span>
            <input
              type="search"
              placeholder="Search terms, formulas, concepts…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{
                paddingLeft: '34px', paddingRight: '12px', paddingTop: '9px', paddingBottom: '9px',
                borderRadius: '8px', border: '1.5px solid var(--border-subtle)',
                background: 'var(--bg-card)', color: 'var(--text-primary)',
                fontSize: '0.82rem', outline: 'none', width: '100%', boxSizing: 'border-box',
                fontFamily: 'var(--font-sans,system-ui)',
                transition: 'border-color 0.2s',
              }}
              onFocus={e => e.target.style.borderColor = '#c9a84c'}
              onBlur={e => e.target.style.borderColor = 'var(--border-subtle)'}
            />
          </div>
        </div>

        {/* Cluster filter pills */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Filter:</span>
          {[{ id: 'all', label: 'All Clusters', color: '#7c7c7c' }, ...CLUSTERS.map(c => ({ id: c.id, label: c.title, color: c.accentColor }))].map(f => (
            <button
              key={f.id}
              onClick={() => setActiveCluster(f.id)}
              style={{
                padding: '4px 12px', borderRadius: '20px', fontSize: 'var(--type-caption)', fontWeight: 700,
                cursor: 'pointer', transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                background: activeCluster === f.id ? f.color : 'transparent',
                color: activeCluster === f.id ? '#fff' : f.color,
                border: `1.5px solid ${f.color}`,
                opacity: activeCluster === f.id ? 1 : 0.7,
              }}
              onMouseOver={e => { if (activeCluster !== f.id) e.currentTarget.style.opacity = '1'; }}
              onMouseOut={e => { if (activeCluster !== f.id) e.currentTarget.style.opacity = '0.7'; }}
            >
              {f.label}
            </button>
          ))}
          {q && <span style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)', marginLeft: 4 }}>{totalVisible} result{totalVisible !== 1 ? 's' : ''}</span>}
        </div>
      </div>

      {/* -- No results -- */}
      {filteredClusters.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '2rem', marginBottom: '12px' }}>??</div>
          <div style={{ fontWeight: 600, marginBottom: '4px' }}>No terms match your search</div>
          <div style={{ fontSize: '0.8rem' }}>Try a different keyword</div>
        </div>
      )}

      {/* -- Clusters -- */}
      {filteredClusters.map(cluster => (
        <section key={cluster.id} style={{ marginBottom: '40px' }}>
          {/* Cluster header */}
          <div style={{
            display: 'flex', alignItems: 'flex-end', gap: '16px',
            paddingBottom: '16px', marginBottom: '20px',
            borderBottom: `2px solid ${cluster.accentColor}33`,
          }}>
            <div style={{ fontSize: '4rem', lineHeight: 1, fontWeight: 900, color: `${cluster.accentColor}18`, letterSpacing: '-0.04em', userSelect: 'none' }}>
              {cluster.number}
            </div>
            <div>
              <div style={{
                fontSize: 'var(--type-caption)', fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase',
                padding: '2px 8px', borderRadius: '3px', display: 'inline-block', marginBottom: '6px',
                background: `${cluster.accentColor}18`, color: cluster.accentColor,
              }}>{cluster.tag}</div>
              <h3 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.1 }}>
                {cluster.title}
              </h3>
              <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'italic', maxWidth: '560px' }}>
                {cluster.desc}
              </p>
            </div>
          </div>

          {/* Term cards */}
          {cluster.terms.map(term => (
            <TermCard key={term.id} term={term} clusterAccent={cluster.accentColor} searchQuery={q} />
          ))}
        </section>
      ))}

      {/* Footer note */}
      <div style={{
        marginTop: '32px', padding: '12px 16px', borderRadius: '8px',
        background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
        fontSize: 'var(--type-caption)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono,monospace)',
        letterSpacing: '0.04em',
      }}>
        ?? Verified against engine.py, round_logic.py, round2_csrd.py · Muressons Global Corporation — Build 2026-R10
      </div>
    </div>
  );
}
