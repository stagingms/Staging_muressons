"""
Section 16: Full Game Walkthrough — Climate Black Swan Pathway
Helper module imported by generate_briefings_doc.py
"""
from docx.shared import Pt


def write_section_14(doc, add_styled_heading, add_body, add_bullet):
    """Write Section 16 into the Word document."""

    add_styled_heading(doc, '16. Full Game Walkthrough: Climate Black Swan (Rounds 1-10)', level=1)
    add_body(doc, (
        'This section walks through a complete 10-round game using the Advanced Climate '
        'decision paradigm with the Climate Black Swan ending pathway. For each round we show: '
        'the decision chosen, investment allocations, which engine formulas fire, step-by-step '
        'calculations, and the resulting state changes. Starting state: Treasury $50M, 4 BUs '
        '(Pharma Rev $18M/OPEX $11M, Electronics $22M/$14M, Consumer Goods $15M/$9M, '
        'Software $20M/$8M), Synergy 1.00, Group Rep 60, avg SLO 70, avg Burnout 30, '
        'avg Carbon Intensity 55, Workforce Readiness 50.'
    ))

    rounds_data = [
        {
            'num': 1, 'title': 'Foundations — ESG Baseline Assessment',
            'choice': 'Option B: Deep Forensic Audit',
            'choice_rationale': 'Pays $3M upfront but uncovers hidden risks, sets deep_audit_completed flag, and reduces CI by 5.',
            'investment': 'Balanced 0.20 across all BUs + HR pillar. Total CAPEX ~$15M.',
            'formulas': [
                ('Synergy Engine (11.3)', 'Ratio=0.20 > 0.10 threshold => DEFERRED 1 round. No OPEX savings this round.'),
                ('Implementation Lag (12.3)', 'All 4 BUs queued for R2 delivery. Immediate cost: $15M CAPEX.'),
                ('Inflation (11.9)', 'All OPEX * 1.025: Pharma $11M->$11.275M, Elec $14M->$14.35M, CG $9M->$9.225M, SW $8M->$8.2M'),
                ('CSF (11.1)', 'Gross Profit = (18-11.275)+(22-14.35)+(15-9.225)+(20-8.2) = 6.73+7.65+5.78+11.8 = $31.95M'),
                ('Loan Check', 'CAPEX $15M > 20% of $50M ($10M) => Loan $5M at 12% => Interest $600K'),
                ('Option Impact', 'Treasury -$3M (audit cost), Rep +5 (all BUs), CI -5 (all BUs)'),
                ('Burnout (11.14)', 'HR High: burnout 30 - 10 = 20. Readiness 50 + 8 = 58.'),
            ],
            'state_after': 'Treasury: $50M + $31.95M - $0.6M - $3M = $78.35M. CI: 55-5=50. Rep: 65. Burnout: 20. Readiness: 58.',
        },
        {
            'num': 2, 'title': 'Double Materiality — CSRD Alignment',
            'choice': 'Option A: Full Materiality Alignment',
            'choice_rationale': 'Sets materiality_aligned flag (+0.10 M_R at R10). Revenue hit -$2.5M but governance risk -5, Rep +5, CI -3.',
            'investment': 'Balanced 0.20 + HR pillar. CAPEX ~$15M. R1 deferred synergy projects complete.',
            'formulas': [
                ('Deferred Synergy Completes', 'R1 projects deliver: Pharma OPEX $11.275M * (1-0.312) = $7.76M savings queued now apply'),
                ('Synergy Engine', 'New R2 investments (0.20) deferred again to R3.'),
                ('Inflation', 'OPEX * 1.025 applied before synergy.'),
                ('NCD Forgiveness (AC mode)', 'Green CAPEX $15M => forgiveness = 2.0 * ln(1+15) = 2.0 * 2.77 = 5.55 NCD reduction per BU'),
                ('Materiality Gate', 'CFO gate active: investments must align with high-impact quadrant. Accuracy bonus $2M if >90%.'),
                ('Option Impact', 'Revenue -$2.5M, Rep +5, Gov Risk -5, CI -3. AC bonus: NCD forgiveness * 1.25'),
                ('Burnout', 'HR High: 20 - 10 = 10. Readiness: 58 + 8 = 66.'),
            ],
            'state_after': 'Treasury: ~$91M. CI: 50-3=47. Rep: 70. Burnout: 10. Readiness: 66. Flags: deep_audit, materiality_aligned.',
        },
        {
            'num': 3, 'title': 'Scope 3 Emissions — Supply Chain Decarbonisation',
            'choice': 'Option A: Rapid Supplier Switch',
            'choice_rationale': 'Sets early_decarboniser flag (needed for Adaptation Premium +0.20 M_R at R10). CI -15, Treasury -$4M.',
            'investment': 'Balanced 0.15 + HR pillar. CAPEX ~$11.25M.',
            'formulas': [
                ('Synergy Engine', 'Ratio 0.15 > 0.10 => deferred. R2 deferred projects completing this round.'),
                ('CBAM Border Adj (AC)', 'R3 is supply chain round. avg CI=47 > 40 threshold => import surcharge applies.'),
                ('NCD Forgiveness', '2.0 * ln(1+11.25) = 2.0 * 2.51 = 5.02 NCD reduction per BU'),
                ('Option Impact', 'Treasury -$4M, CI -15, Revenue -$800K. supply_chain_disruption risk flag active.'),
                ('Burnout', 'HR High: 10 - 10 = 0 (floored). Readiness: 66 + 8 = 74.'),
                ('VRIO Decay (11.5)', 'Synergy 1.00 * 0.95 = 0.95 (decay). No synergy boost yet.'),
            ],
            'state_after': 'Treasury: ~$94M. CI: 47-15=32. Rep: 70. Burnout: 0. Readiness: 74. Flags: +early_decarboniser.',
        },
        {
            'num': 4, 'title': 'Contagion — Reputation Crisis Cascade',
            'choice': 'Option A: Full Transparency & Remediation',
            'choice_rationale': 'Costs $6M but Rep +10, SLO +8, CI -4. Prevents contagion amplification from deep_audit flag.',
            'investment': 'Balanced 0.20 + HR pillar. CAPEX ~$15M.',
            'formulas': [
                ('Contagion Engine (11.2)', 'Base severity=40. deep_audit flag present => NO doubling (blindspot not set).'),
                ('Contagion Calc', 'sigmoid((40-30)/15) = sigmoid(0.667) = 0.661. Group Rep = 70 - 50*0.661 = 70-33.05 = 36.95'),
                ('Option A Remediation', 'Rep +10, SLO +8 applied AFTER contagion => Rep recovers to ~47, then option brings to ~57'),
                ('Stakeholder Fatigue (11.13)', 'crisis_count=1. Recovery efficiency = 1/(1+0.3*1) = 0.769'),
                ('Burnout', 'HR High: 0 - 10 = 0 (floored). Readiness: 74 + 8 = 82.'),
                ('Loan Check', 'CAPEX $15M, free CSF ~$18.8M => no loan needed.'),
            ],
            'state_after': 'Treasury: ~$85M. CI: 32-4=28. Rep: ~57. SLO: ~76. Burnout: 0. Readiness: 82.',
        },
        {
            'num': 5, 'title': 'Climate — Physical Climate Risk Event',
            'choice': 'Option B: Nature-Based Solutions',
            'choice_rationale': 'Sets nature_based_resilience flag (needed for Adaptation Premium). Resilience 0.60 but deferred 2 rounds. NCD -8, CI -6.',
            'investment': 'Balanced 0.15 + HR pillar. CAPEX ~$11.25M.',
            'formulas': [
                ('Stochastic Climate (11.20)', 'Roll = 0.62 < 0.75 threshold => CYCLONE STRIKES.'),
                ('Resilience Factor', 'Option B resilience=0.60 BUT deferred 2 rounds => effective=0.0 THIS round.'),
                ('Cyclone Damage', 'Damage = $12M * (1 - 0.0) = $12M. Treasury hit: -$12M.'),
                ('Option Cost', 'Treasury -$5M (nature-based infrastructure). NCD -8 per BU. CI -6.'),
                ('Foreshadowing', 'Climate Black Swan R5: "IPCC Special Report: 1.5C Overshoot Now Likely" appears in news feed.'),
                ('Climate Tipping Check', 'avg CI=28-6=22 < 70 => no tipping point escalation.'),
                ('Burnout', 'HR High: 0 (floor). Readiness: 82 + 8 = 90.'),
            ],
            'state_after': 'Treasury: ~$65M (cyclone hit). CI: 22. Rep: ~57. SLO: ~76. Burnout: 0. Readiness: 90. Flags: +nature_based_resilience.',
        },
        {
            'num': 6, 'title': 'AI Bias — Algorithmic Ethics',
            'choice': 'Option B: Ethical AI Overhaul',
            'choice_rationale': 'Sets ethical_ai_overhaul flag (+0.15 M_R, +2.5 Ethical Reasoning score). SLO +15, Rep +5. Cost $8M.',
            'investment': 'Balanced 0.15 + HR pillar. CAPEX ~$11.25M.',
            'formulas': [
                ('Option Impact', 'Treasury -$8M, SLO +15, Rep +5, CI -4, Revenue +$800K.'),
                ('Truth Premium', 'ethical_ai_overhaul flag queued as pending project (truth_premium type).'),
                ('Foreshadowing', 'Climate Black Swan R6: "Carbon Futures Surge 40%" appears.'),
                ('Synergy Engine', 'Ratio 0.15 deferred. Previous rounds completing.'),
                ('NCD Forgiveness (AC)', '2.0 * ln(1+11.25) = 5.02 per BU.'),
                ('Burnout', 'HR High: 0 (floor). Readiness: 90 + 8 = 98 (near cap).'),
            ],
            'state_after': 'Treasury: ~$57M. CI: 22-4=18. Rep: ~62. SLO: ~88. Burnout: 0. Readiness: 98. Flags: +ethical_ai_overhaul.',
        },
        {
            'num': 7, 'title': 'Circularity — Circular Economy Transition',
            'choice': 'Option C: Waste-to-Energy Partnership',
            'choice_rationale': 'Sets synergy_unlock + waste_to_energy flags (+0.30 M_R). Synergy boost +0.30. NCD -4, CI -6.',
            'investment': 'Balanced 0.25 + HR pillar. CAPEX ~$18.75M.',
            'formulas': [
                ('Synergy Boost', 'synergy_multiplier += 0.30. With readiness 98 (>75): bonus scaling * 1.10.'),
                ('Effective Boost', 'Boost = 0.30 * 1.10 = 0.33. Synergy: 0.95 * 0.95^2 (VRIO decay R3-R6) + 0.33 = ~0.86 + 0.33 = 1.19'),
                ('R5 Resilience Matures', 'Nature-based solutions complete (2-round lag from R5). Resilience factor now 0.60 active.'),
                ('Foreshadowing', 'Climate Black Swan R7: "Insurance Consortium: Uninsurable Assets by 2035"'),
                ('Option Cost', 'Treasury -$7M. NCD -4 per BU. CI -6.'),
                ('NCD Forgiveness', '2.0 * ln(1+18.75) = 5.96 per BU. Green Fund contribution.'),
                ('Burnout', 'HR High: 0 (floor). Readiness: 100 (capped).'),
            ],
            'state_after': 'Treasury: ~$55M. CI: 18-6=12. Synergy: ~1.19. Rep: ~65. SLO: ~88. Readiness: 100.',
        },
        {
            'num': 8, 'title': 'Blue Stress — Water Scarcity Emergency',
            'choice': 'Option A: Water Efficiency for All BUs',
            'choice_rationale': 'Equitable adaptation. SLO +5, CI -3. Avoids electronics_water_priority flag (preserves Resilience Bonus +0.20 M_R).',
            'investment': 'Balanced 0.20 + HR pillar. CAPEX ~$15M.',
            'formulas': [
                ('Option Cost', 'Treasury -$12M. Water dependency -20. SLO +5. CI -3.'),
                ('Foreshadowing', 'Climate Black Swan R8: "ALERT: 1.5C Threshold Breached — Carbon Markets in Turmoil"'),
                ('Stranded Asset Check', 'avg CI=12-3=9 < 120 => no stranded asset CoC penalty. Major advantage.'),
                ('Brain-Drain (11.6)', 'Group Rep ~65 => exactly at threshold. No brain-drain penalty (threshold is < 65).'),
                ('Synergy Engine', 'With synergy 1.19, ratio 0.20: effective = sqrt(0.20)*0.7*1.19 = 0.447*0.7*1.19 = 0.372. OPEX * 0.628.'),
                ('Burnout', 'HR High: 0 (floor). Readiness: 100 (capped). HR invested 8/8 rounds.'),
            ],
            'state_after': 'Treasury: ~$46M. CI: 9. Synergy: 1.19. Rep: ~67. SLO: ~90. Burnout: 0. Readiness: 100.',
        },
        {
            'num': 9, 'title': 'Just Transition — Workforce & Community Justice',
            'choice': 'Option C: Community Investment Fund',
            'choice_rationale': 'Sets community_fund flag (+0.18 M_R). SLO +18, Rep +12. Cost $20M but avoids strike risk.',
            'investment': 'Balanced 0.15 + HR pillar. CAPEX ~$11.25M.',
            'formulas': [
                ('Strike Probability (11.7)', 'Option C chosen (not immediate closure) => no strike check needed.'),
                ('Regulatory Friction (11.21)', 'avg SLO ~90 > 50 => minimal friction. OPEX surcharge negligible.'),
                ('JT Scaling', 'HR invested 9/9 rounds => jt_scaling = 1.0 + 9*0.10 = 1.90, capped at 1.50.'),
                ('JT M_R Boost', 'community_fund base +0.18 * 1.50 = 0.27. Extra = 0.27 - 0.18 = +0.09 bonus from HR consistency.'),
                ('Option Impact', 'Treasury -$20M. SLO +18. Rep +12. CI -3. Gov risk -5.'),
                ('Burnout', 'HR High: 0 (floor). Readiness: 100 (capped). HR invested 9/9.'),
            ],
            'state_after': 'Treasury: ~$28M. CI: 9-3=6. Rep: ~77. SLO: ~95. Burnout: 0. Readiness: 100.',
        },
        {
            'num': 10, 'title': 'Grand Finale — Climate Black Swan: The Stranded Asset Reckoning',
            'choice': 'Option A: Emergency Decarbonisation',
            'choice_rationale': 'CI halved (6/2=3), NCD halved. Cost $20M but positions for Climate Leader bonus (+0.30 M_R).',
            'investment': 'Balanced 0.10. CAPEX ~$7.5M. Final round — deferred projects will not mature.',
            'formulas': [
                ('Option A Impact', 'Treasury -$20M. All BU CI halved: 6/2 = 3. NCD halved.'),
                ('Carbon Tax (Climate)', '$750/ton (tripled from standard $250). Carbon Tonnage = sum(CI * Rev / 1M).'),
                ('Carbon Tonnage', 'CI=3 across 4 BUs. Tonnage = 4 * (3 * ~$19M / 1M) = 4 * 57 = 228 tons.'),
                ('Carbon Cost', '228 * $750 = $171,000 (very low due to aggressive decarbonisation).'),
                ('Terminal EBITDA', 'Revenue ~$76M - OPEX ~$30M (synergy-reduced) - Carbon $0.17M = ~$45.8M'),
                ('Exit Multiple (CI Haircut)', 'avg CI=3 < 25 => no haircut. Exit Multiple = 12.0x.'),
            ],
            'state_after': 'See Terminal Valuation below.',
        },
    ]

    for rd in rounds_data:
        add_styled_heading(doc, f'16.{rd["num"]} Round {rd["num"]}: {rd["title"]}', level=2)

        p = doc.add_paragraph()
        run = p.add_run(f'Decision: {rd["choice"]}')
        run.bold = True
        run.font.size = Pt(11)
        add_body(doc, rd['choice_rationale'])

        add_body(doc, f'Investment: {rd["investment"]}')
        add_body(doc, 'Formulas & Calculations:', bold=True)
        for fname, fcalc in rd['formulas']:
            add_bullet(doc, f'{fname}: {fcalc}')

        p = doc.add_paragraph()
        run = p.add_run(f'State After R{rd["num"]}: ')
        run.bold = True
        run.font.size = Pt(10)
        run = p.add_run(rd['state_after'])
        run.font.size = Pt(10)
        doc.add_paragraph()

    # Terminal Valuation
    add_styled_heading(doc, '16.11 Terminal Valuation Calculation', level=2)
    add_body(doc, 'Step 1 — Terminal EBITDA:', bold=True)
    add_bullet(doc, 'Total Revenue (4 BUs, synergy-enhanced): ~$76M')
    add_bullet(doc, 'Total OPEX (synergy-reduced, inflation-adjusted): ~$30M')
    add_bullet(doc, 'Carbon Tonnage: 228 tons at $750/ton = $171K')
    add_bullet(doc, 'Terminal EBITDA = $76M - $30M - $0.17M = $45.83M')

    add_body(doc, 'Step 2 — Green Fund Balance:', bold=True)
    add_bullet(doc, 'Accumulated from AC mode green CAPEX contributions: ~$4M')
    add_bullet(doc, 'EBITDA + Green Fund = $45.83M + $4M = $49.83M')

    add_body(doc, 'Step 3 — Regenerative Multiple (M_R):', bold=True)

    mr_table = doc.add_table(rows=1, cols=3)
    mr_table.style = 'Light Grid Accent 1'
    hdr = mr_table.rows[0].cells
    for i, label in enumerate(['Component', 'Value', 'Source']):
        hdr[i].text = label
        for p2 in hdr[i].paragraphs:
            for r2 in p2.runs:
                r2.bold = True
                r2.font.size = Pt(9)
    mr_items = [
        ('Base', '+1.00', 'Always'),
        ('CSRD Governance (R2A)', '+0.10', 'materiality_aligned flag'),
        ('Truth Premium (R6B)', '+0.15', 'ethical_ai_overhaul flag'),
        ('Synergy Bonus (R7C)', '+0.30', 'synergy_unlock flag'),
        ('Resilience Bonus (R5B+R8A)', '+0.20', 'No insurance_only, no electronics_water_priority'),
        ('Community Champion (R9C)', '+0.18', 'community_fund flag (base)'),
        ('JT Scaling Bonus', '+0.09', 'HR invested 9/9 rounds => 1.50x scaling on 0.18'),
        ('Workforce Excellence', '+0.10', 'workforce_readiness=100 >= 75'),
        ('Wellbeing Champion', '+0.05', 'avg burnout=0 < 20'),
        ('Instability Discount', '+0.00', 'avg SLO=95 >= 75 => NO penalty'),
        ('Climate Leader (pathway)', '+0.30', 'avg CI=3 < 25'),
        ('Adaptation Premium (pathway)', '+0.20', 'nature_based_resilience + early_decarboniser'),
        ('Carbon Transition (pathway)', '+0.15', 'CI reduced from 55 to 3 = 94.5% reduction >= 40%'),
        ('Stranded Asset Penalty', '+0.00', 'avg CI=3 < 50 => NO penalty'),
    ]
    for item in mr_items:
        row = mr_table.add_row().cells
        for i2, val in enumerate(item):
            row[i2].text = val
            for p2 in row[i2].paragraphs:
                for r2 in p2.runs:
                    r2.font.size = Pt(9)

    add_body(doc, '')
    add_bullet(doc, 'Total M_R = 1.00 + 0.10 + 0.15 + 0.30 + 0.20 + 0.18 + 0.09 + 0.10 + 0.05 + 0.30 + 0.20 + 0.15 = 2.82')
    add_bullet(doc, 'Profile: Climate Pioneer (Regenerative Titan tier, M_R >= 1.80)')

    add_body(doc, 'Step 4 — Exit Multiple:', bold=True)
    add_bullet(doc, 'Base: 12.0x')
    add_bullet(doc, 'CI Haircut: avg CI=3 < 25 => haircut = max(0, (3-25)*0.01) = 0. No haircut.')
    add_bullet(doc, 'Final Exit Multiple = 12.0x')

    add_body(doc, 'Step 5 — Terminal Value:', bold=True)
    add_bullet(doc, 'TV = (EBITDA + Green Fund) * Exit Multiple * M_R')
    add_bullet(doc, 'TV = $49.83M * 12.0 * 2.82')
    add_bullet(doc, 'TV = $49.83M * 33.84 = $1,686M')

    p = doc.add_paragraph()
    run = p.add_run('Result: Terminal Value of ~$1.69 BILLION — Climate Pioneer archetype.')
    run.bold = True
    run.font.size = Pt(12)

    doc.add_paragraph()
    add_body(doc, 'Step 6 — Competency Scores (Data-Derived):', bold=True)
    add_bullet(doc, 'Strategic Thinking: (M_R 2.82 - 0.5) / 0.15 = 15.5 -> capped at 10.0/10')
    add_bullet(doc, 'Stakeholder Empathy: SLO 95/10 + burnout bonus (0<30: +2) = 9.5 + 2.0 -> 10.0/10')
    add_bullet(doc, 'Financial Acumen: Treasury $8M/$5M + EBITDA $45.8M/$10M = 1.6 + 4.58 = 6.2/10')
    add_bullet(doc, 'Ethical Reasoning: 4.0 + 2.5 (ethical_ai) + 2.0 (community_fund) + 1.0 (deep_audit) = 9.5/10')
    add_bullet(doc, 'Systems Thinking: (synergy 1.19 - 0.7)*10 + VRIO ~65/20 = 4.9 + 3.25 = 8.2/10')
    add_bullet(doc, 'Adaptive Leadership: readiness 100/15 + HR rounds 9*1.0 = 6.67 + 9.0 -> 10.0/10')
    add_bullet(doc, 'Note: Financial Acumen is lower (6.2) because heavy ethical/community investment reduced treasury. This is by design — the simulation tests whether players prioritise financial hoarding or stakeholder value.')

    doc.add_paragraph()
    add_body(doc, 'Key Teaching Moments for Facilitators:', bold=True)
    add_bullet(doc, 'R1: Deep audit cost ($3M) prevents R4 contagion doubling — a $30M+ swing. Early diagnostic investment pays off.')
    add_bullet(doc, 'R3: early_decarboniser flag is invisible until R10 where it unlocks +0.20 Adaptation Premium. Systems thinking reward.')
    add_bullet(doc, 'R5: Cyclone hits at full damage ($12M) despite choosing nature-based solutions — the 2-round lag is the lesson.')
    add_bullet(doc, 'R7: Synergy boost scaled by workforce readiness. 9 rounds of HR investment amplifies the R7 payoff by 10%.')
    add_bullet(doc, 'R9: JT scaling rewards HR consistency — 9 rounds of investment turns +0.18 M_R into +0.27 M_R.')
    add_bullet(doc, 'R10: Climate Black Swan carbon tax ($750/ton) would devastate high-CI players. At CI=3, carbon cost is just $171K vs ~$28M for a player at CI=50.')
    add_bullet(doc, 'The ~$1.6B gap between Climate Pioneer and a neglect player (~$86M Stranded Relic) demonstrates that every round matters.')
