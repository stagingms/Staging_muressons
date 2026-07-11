"""Enhanced §3: Mathematical Engine Reference with formulas, examples, teaching tips."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from docx_styles import *

def build_architecture_diagram(doc):
    """Insert the Simulation Architecture Map at the start of Part 1."""
    doc.add_heading('Simulation Architecture Map', level=2)
    doc.add_paragraph('The diagram below illustrates the complete simulation pipeline — from player decisions through the mathematical engine to terminal valuation outputs.')
    add_screenshot_placeholder(doc, 'Simulation Architecture Map — engine pipeline flowchart')

def build_section3_enhanced(doc):
    add_page_break(doc)
    doc.add_heading(u'§3. Mathematical Engine Reference', level=1)
    doc.add_paragraph('This section documents every mathematical engine in the simulation. For each engine: the exact formula from the codebase, a worked sample calculation, and a non-mathematical teaching analogy for facilitators to use with students.')
    add_callout(doc, 'These formulas are HIDDEN from players. They are the facilitator\'s "answer key" for understanding why outcomes occur. Never reveal formulas during gameplay — reveal them during debrief.', 'warning')
    add_screenshot_placeholder(doc, 'Simulation Architecture flowchart showing process_tick() pipeline')

    # ── ENGINE 1: CSF ──
    doc.add_heading('3.1 Corporate Strategic Fund (CSF)', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('CSF = Sum(Revenue_Base - OPEX_Base) - Dividends_Paid'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    doc.add_paragraph('The CSF calculates net cash generated each round from all BU operations minus any board-mandated dividend payments. This is the primary source of corporate treasury growth.')
    doc.add_heading('Sample Calculation', level=3)
    add_styled_table(doc, ['BU', 'Revenue', 'OPEX', 'Gross Profit'],
        [['Pharma', '$18.0M', '$12.0M', '$6.0M'], ['Electronics', '$16.5M', '$11.5M', '$5.0M'],
         ['Consumer Goods', '$10.5M', '$7.5M', '$3.0M'], ['Software', '$8.5M', '$5.5M', '$3.0M'],
         ['TOTAL', '$53.5M', '$36.5M', '$17.0M']])
    doc.add_paragraph('With $0 dividends: CSF = $17.0M added to treasury. With $2M dividends: CSF = $15.0M.')
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "Think of CSF as your corporate paycheck. Every round, your four businesses generate profit. But just like a household budget, you have fixed obligations (dividends to shareholders). What\'s left is what you can invest. The question is: how do you allocate a finite paycheck across competing priorities?"', 'tip')

    # ── ENGINE 2: CONTAGION ──
    doc.add_heading('3.2 Contagion Engine (Sigmoid Model)', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('Group_Rep = Avg_BU_Rep - 50 x sigmoid((severity - 30) / 15)'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    p2 = doc.add_paragraph(); r2 = p2.add_run('Where sigmoid(x) = 1 / (1 + e^(-x))'); r2.font.name = 'Consolas'; r2.font.size = Pt(10)
    doc.add_paragraph('The sigmoid (S-curve) models non-linear crisis propagation: small crises are absorbed with minimal damage, but once severity crosses a threshold (~30), damage escalates rapidly before saturating at extreme levels. The electronics_blindspot flag DOUBLES severity from 40 to 80.')
    doc.add_heading('Sample Calculation', level=3)
    add_styled_table(doc, ['Scenario', 'R1 Choice', 'Severity', 'Sigmoid Input', 'Sigmoid Output', 'Rep Hit', 'Final Rep'],
        [['Deep Audit (no blindspot)', 'B', '40', '(40-30)/15 = 0.67', '0.66', '-33.0', '22.0'],
         ['Phased Audit (deferred)', 'C', '60', '(60-30)/15 = 2.0', '0.88', '-44.0', '11.0'],
         ['Surface Scan (blindspot)', 'A', '80', '(80-30)/15 = 3.33', '0.97', '-48.3', '6.7']])
    doc.add_paragraph('Starting avg rep = 55. The blindspot team loses 48.3 points vs. 33.0 for the audited team — a 46% worse outcome from a single R1 decision. This is the simulation\'s most consequential hidden mechanic.')
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "Think of reputation damage like a viral infection. A small scandal (low severity) is like a common cold — your immune system handles it. But a major scandal (high severity) is like a pandemic — it overwhelms your defences. The S-curve shows that there\'s a tipping point where manageable becomes catastrophic. The R1 audit was your vaccine — those who skipped it caught the full disease at R4."', 'tip')

    # ── ENGINE 3: SYNERGY ──
    doc.add_heading('3.3 Synergy Engine (Square-Root Scaling)', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('effective_ratio = sqrt(investment_ratio) x 0.7'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    p2 = doc.add_paragraph(); r2 = p2.add_run('New_OPEX = Old_OPEX x (1 - effective_ratio x synergy_multiplier)'); r2.font.bold = True; r2.font.name = 'Consolas'; r2.font.size = Pt(10)
    doc.add_paragraph('Square-root scaling means the first dollar invested yields the highest return, with each subsequent dollar yielding progressively less. At 25% investment ratio, you get 50% of max efficiency. At 100%, you get 70%. This prevents "solve by spending" strategies.')
    doc.add_heading('Sample Calculation', level=3)
    add_styled_table(doc, ['Investment Ratio', 'sqrt(ratio)', 'Effective Ratio', 'OPEX Reduction (syn=1.0)', 'Comment'],
        [['10%', '0.316', '0.221', '-22.1%', 'Excellent ROI per dollar'],
         ['25%', '0.500', '0.350', '-35.0%', 'Good balance'],
         ['50%', '0.707', '0.495', '-49.5%', 'Diminishing returns begin'],
         ['100%', '1.000', '0.700', '-70.0%', 'Maximum efficiency (capped at 70%)']])
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "Imagine you\'re watering a garden. The first bucket of water makes a huge difference to dry soil. The second bucket helps, but less. By the tenth bucket, the ground is saturated and you\'re wasting water. That\'s diminishing returns. Your investment in cross-BU synergy works the same way — focus beats dilution."', 'tip')

    # ── ENGINE 4: NCD ──
    doc.add_heading('3.4 Natural Capital Debt (NCD) Compounding', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('Interest_Rate = Base_Rate + (NCD x 0.0001)'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    p2 = doc.add_paragraph(); r2 = p2.add_run('NCD_new = NCD_current x (1 + Interest_Rate) + round_delta'); r2.font.bold = True; r2.font.name = 'Consolas'; r2.font.size = Pt(10)
    doc.add_paragraph('At NCD=100, interest rate is ~6%. At NCD=500, it climbs to ~10%. This creates a "debt trap" — the more ecological damage you accumulate, the faster it compounds. NCD is deducted from terminal value as an ecological liability.')
    doc.add_heading('Sample Calculation', level=3)
    doc.add_paragraph('Electronics BU starts with NCD = 200. Assume no investment (round_delta = 0):')
    add_styled_table(doc, ['Round', 'NCD Start', 'Rate', 'Interest', 'NCD End'],
        [['R1', '200.0', '6.02%', '+12.0', '212.0'],
         ['R3', '225.1', '6.03%', '+13.6', '238.7'],
         ['R5', '252.6', '6.03%', '+15.2', '267.8'],
         ['R7', '283.4', '6.03%', '+17.1', '300.5'],
         ['R10', '337.5', '6.03%', '+20.3', '357.8']])
    doc.add_paragraph('Over 10 rounds of neglect, NCD grows 79% from compounding alone — a $15.8M terminal value penalty at $100K per NCD point.')
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "NCD works exactly like credit card debt. If you only make minimum payments, the balance grows faster than you can pay it off. Nature is lending you ecosystem services — clean water, stable climate, pollination. Every round you don\'t repay, the interest compounds. By R10, teams that ignored NCD owe nature a debt they can never repay."', 'tip')

    # ── ENGINE 5: VRIO DECAY ──
    doc.add_heading('3.5 VRIO Competitive Advantage Decay', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('VRIO_next = VRIO_current x (1 - decay_rate)'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    doc.add_paragraph('Default decay_rate = 0.05 (5% per round). VRIO starts at 0.80 and decays towards 0.50 (industry average). Investing in a BU resets or slows decay. VRIO modifies BU revenue effectiveness.')
    doc.add_heading('Sample Calculation', level=3)
    doc.add_paragraph('Starting VRIO = 0.80 with no investment for 5 rounds:')
    doc.add_paragraph('R1: 0.80 x 0.95 = 0.76 | R2: 0.72 | R3: 0.69 | R4: 0.65 | R5: 0.62')
    doc.add_paragraph('After 5 rounds of neglect, competitive advantage drops from "strong" (0.80) to "average" (0.62). This represents competitor imitation eroding your unique capabilities.')
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "Your competitive advantage is like a moat around a castle. If you don\'t maintain it, competitors slowly fill it in. VRIO measures how unique and valuable your capabilities are. Without active investment, competitors copy your best practices, hire your talent, and erode your edge. Standing still means falling behind."', 'tip')

    # ── ENGINE 6: BURNOUT ──
    doc.add_heading('3.6 Burnout Engine (Quadratic OPEX Penalty)', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('Penalty_Rate = ((burnout - 20)^2) x 0.000028125'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    p2 = doc.add_paragraph(); r2 = p2.add_run('OPEX_new = OPEX x (1 + Penalty_Rate)'); r2.font.bold = True; r2.font.name = 'Consolas'; r2.font.size = Pt(10)
    doc.add_paragraph('Burnout follows a quadratic (squared) curve — costs accelerate as burnout increases. Below 20, there is no penalty. Above 20, costs grow exponentially. At 70+, burnout also increases R9 strike probability.')
    doc.add_paragraph('Natural drift: +6 burnout per round if no HR investment. HR investment: -16 to -30 burnout.')
    doc.add_heading('Sample Calculation', level=3)
    add_styled_table(doc, ['Burnout', 'Penalty Calc', 'OPEX Penalty', 'On $12M OPEX', 'Risk Level'],
        [['20%', '(0)^2 x 0.000028 = 0%', '+0%', '$0', 'Safe'],
         ['40%', '(20)^2 x 0.000028 = 1.1%', '+1.1%', '+$135K', 'Watch'],
         ['60%', '(40)^2 x 0.000028 = 4.5%', '+4.5%', '+$540K', 'Critical'],
         ['80%', '(60)^2 x 0.000028 = 10.1%', '+10.1%', '+$1.2M', 'Emergency'],
         ['100%', '(80)^2 x 0.000028 = 18.0%', '+18.0%', '+$2.2M', 'Catastrophic']])
    doc.add_paragraph('A team that ignores HR for 8 rounds (natural drift: 10 + 8x6 = 58%) loses $540K/round in OPEX penalties AND faces 60%+ strike probability at R9.')
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "Burnout is like a pressure cooker. At first, the steam builds slowly and nothing seems wrong. But the pressure follows a squared curve — it accelerates. By the time you notice the lid rattling, it\'s about to blow. The R9 strike is the explosion. The only way to release pressure is HR investment — and the earlier you start, the cheaper it is."', 'tip')

    # ── ENGINE 7: BRAIN-DRAIN ──
    doc.add_heading('3.7 Brain-Drain Engine (Talent Penalty)', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('Talent_Penalty = 1 + max(0, (65 - Group_Rep) / 100) x 1.5'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    p2 = doc.add_paragraph(); r2 = p2.add_run('If burnout > 50: Penalty += ((burnout - 50) / 100) x 2.0'); r2.font.bold = True; r2.font.name = 'Consolas'; r2.font.size = Pt(10)
    doc.add_paragraph('Applies to Software (and Technology/Banking verticals). When reputation drops below 65, talent leaves for competitors, increasing OPEX as the company must hire expensive contractors/agencies.')
    doc.add_heading('Sample Calculation', level=3)
    add_styled_table(doc, ['Reputation', 'Burnout', 'Penalty Calc', 'OPEX Multiplier', 'On $5.5M OPEX'],
        [['65+', 'Any', '1 + 0 = 1.0', '1.00x', '$5.5M (no penalty)'],
         ['50', '30', '1 + (15/100)x1.5 = 1.225', '1.23x', '$6.7M (+$1.2M)'],
         ['35', '60', '1 + (30/100)x1.5 + (10/100)x2 = 1.65', '1.65x', '$9.1M (+$3.6M)'],
         ['20', '80', '1 + (45/100)x1.5 + (30/100)x2 = 2.28', '2.28x', '$12.5M (+$7.0M)']])
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "Your best engineers have options. When your company\'s reputation drops, they get headhunted by competitors with better brands. You\'re left hiring expensive consultants and agencies to fill the gaps. This is the \'war for talent\' made real. The vicious cycle: low reputation means talent leaves, which means higher costs, which means less investment, which means lower reputation."', 'tip')

    # ── ENGINE 8: INFLATION ──
    doc.add_heading('3.8 Macroeconomic Inflation Engine', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('OPEX_new = OPEX x (1 + inflation_index)'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    doc.add_paragraph('Default inflation_index = 0.05 (5% per 6-month round, ~10% annualised). Inflation silently erodes purchasing power every round. Players must invest just to maintain the status quo.')
    doc.add_heading('Sample Calculation', level=3)
    doc.add_paragraph('Pharma OPEX = $12M. After 10 rounds of 5% inflation: $12M x 1.05^10 = $19.5M — a 63% increase in operating costs that players often fail to anticipate.')
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "Inflation is the silent tax on inaction. Every round, everything gets 5% more expensive. If you don\'t grow revenue faster than inflation grows costs, you\'re actually shrinking. This mirrors the real-world challenge every CEO faces: the treadmill effect."', 'tip')

    # ── ENGINE 9: CASH CONVERSION ──
    doc.add_heading('3.9 Cash Conversion Drag', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('Cash_Efficiency = 1.0 - (governance_risk / 500)'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    p2 = doc.add_paragraph(); r2 = p2.add_run('Realized_Revenue = Revenue x Cash_Efficiency  (clamped to [0.5, 1.0])'); r2.font.bold = True; r2.font.name = 'Consolas'; r2.font.size = Pt(10)
    doc.add_paragraph('BUs with high governance risk convert revenue to cash less efficiently — representing delayed payments, compliance costs, legal reserves, and investor distrust.')
    doc.add_heading('Sample Calculation', level=3)
    add_styled_table(doc, ['Governance Risk', 'Cash Efficiency', 'On $16.5M Revenue', 'Revenue Lost'],
        [['10 (low)', '1.0 - 10/500 = 0.98', '$16.2M', '-$0.3M'],
         ['30 (medium)', '1.0 - 30/500 = 0.94', '$15.5M', '-$1.0M'],
         ['60 (high)', '1.0 - 60/500 = 0.88', '$14.5M', '-$2.0M'],
         ['100 (critical)', '1.0 - 100/500 = 0.80', '$13.2M', '-$3.3M']])
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "Think of governance risk as friction in your financial plumbing. Good governance means revenue flows smoothly into cash. Bad governance creates leaks — legal costs, delayed approvals, compliance penalties, investor distrust. The cash is technically yours, but you can\'t use it all. This is why the \'free\' options (Deny & Deflect) are never truly free."', 'tip')

    # ── ENGINE 10: STRIKE PROBABILITY ──
    doc.add_heading('3.10 Strike Probability Engine', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('P_Strike = Base_Risk + ((1 - SLO/100) x 0.4)'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    p2 = doc.add_paragraph(); r2 = p2.add_run('If burnout > 50: P_Strike += min(0.20, (burnout - 50)/100 x 0.40)'); r2.font.bold = True; r2.font.name = 'Consolas'; r2.font.size = Pt(10)
    doc.add_paragraph('Strike probability is the "time bomb" of the simulation. It combines social licence deficit with workforce burnout to determine the probability of a full revenue wipeout at R9.')
    doc.add_heading('Sample Calculation', level=3)
    add_styled_table(doc, ['SLO', 'Burnout', 'Base Prob', '+ SLO Factor', '+ Burnout Boost', 'Final P(Strike)'],
        [['70', '20', '0.50', '+0.12', '+0.00', '62%'],
         ['50', '40', '0.50', '+0.20', '+0.00', '70%'],
         ['30', '60', '0.50', '+0.28', '+0.04', '82%'],
         ['20', '80', '0.50', '+0.32', '+0.12', '94%']])
    doc.add_paragraph('If a strike triggers, ALL BU revenue for the round is lost. At total revenue of $53.5M, this is catastrophic.')
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "The strike is the ultimate consequence of neglecting your workforce and community. It\'s not random — it\'s the mathematical culmination of every HR decision you made (or didn\'t make) across 8 rounds. The probability formula is your \'labour relations risk score\'. A 94% strike probability means you\'ve treated your workers and community so poorly that a walkout is almost certain."', 'tip')

    # ── ENGINE 11: TERMINAL VALUATION ──
    doc.add_heading('3.11 Terminal Valuation Formula', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('TV = (EBITDA - Carbon_Tax x CO2_Tonnage) x Exit_Multiple x M_R'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    doc.add_paragraph('Where: EBITDA = Sum(Revenue - OPEX), Carbon Tax = $250/ton (adjustable), Exit Multiple = 12.0x, M_R = Regenerative Multiple (1.0 to ~2.1).')
    doc.add_heading('Sample Calculation', level=3)
    doc.add_paragraph('Regenerative Titan scenario:')
    add_bullet_list(doc, [
        'EBITDA: $53.5M revenue - $36.5M OPEX = $17.0M',
        'Carbon Cost: $250 x 25,000 tons = $6.25M',
        'Net: $17.0M - $6.25M = $10.75M',
        'Exit Multiple: 12.0x',
        'M_R: 1.85 (earned most bonuses)',
        'TV = $10.75M x 12.0 x 1.85 = $238.7M',
    ])
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "Terminal Value answers one question: if a buyer wanted to acquire Muressons today, what would they pay? The M_R is the buyer\'s assessment of your sustainability risk. A Titan (M_R 1.85) commands an 85% premium because the buyer sees a future-proof company. A Relic (M_R 0.60) gets a 40% discount because the buyer sees regulatory exposure, stakeholder revolt, and stranded assets."', 'tip')

    # ── ENGINE 12: STAKEHOLDER FATIGUE ──
    doc.add_heading('3.12 Stakeholder Fatigue Engine', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('Recovery_Efficiency = 1.0 / (1 + 0.3 x crisis_count)'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    doc.add_paragraph('After each crisis, stakeholder trust recovery becomes harder. A company facing its 3rd crisis recovers trust at only 53% efficiency. This prevents "crisis → apologise → repeat" strategies.')
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "Trust is like a plate. The first time you drop it, you can glue it back together. The second time, the repair is harder. By the third time, there are so many cracks that it barely holds water. Stakeholders remember every crisis. Each apology is worth less than the last."', 'tip')

    # ── ENGINE 13: SUPPLY CHAIN CONTAGION ──
    doc.add_heading('3.13 Supply Chain Contagion Engine', level=2)
    doc.add_heading('Formula', level=3)
    p = doc.add_paragraph(); r = p.add_run('OPEX_Surcharge = BU_OPEX x Sum(other_BU_gov_risk x 0.002)'); r.font.bold = True; r.font.name = 'Consolas'; r.font.size = Pt(10)
    doc.add_paragraph('BUs with high governance risk contaminate other BUs through shared supplier networks. This models the systemic risk of poor governance spreading through supply chain interdependencies.')
    doc.add_heading('Teaching Tip', level=3)
    add_callout(doc, 'Tell students: "Your supply chains are interconnected. When one BU has poor governance, it creates problems for every other BU that shares suppliers with it. Think of it like a bad neighbour in an apartment building — their problems become your problems through shared infrastructure."', 'tip')
