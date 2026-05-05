"""
Muressons Global Corporation — Student Manual Generator (Part 1)
Sections 1-7: Getting Started, Game Loop, Round Walkthrough
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from student_manual_helpers import *
from round_configs import ROUND_CONFIGS
from pillar_configs import PILLAR_OPTIONS
from ending_pathways import PATHWAY_DESCRIPTIONS, PATHWAY_R10_CONFIGS, FORESHADOWING
from bu_profiles import BU_PROFILES

IMG = os.path.join(os.path.dirname(__file__), 'guide_images')
LIVE = os.path.join(os.path.dirname(__file__), 'live_screenshots')

def build_part1(doc):
    # ══════════════════ TITLE PAGE ══════════════════
    spacer(doc); spacer(doc)
    t = doc.add_heading('Muressons Global Corporation', level=0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in t.runs: r.font.color.rgb = NAVY
    s = doc.add_heading('Student Manual', level=1)
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in s.runs: r.font.color.rgb = TEAL
    spacer(doc)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Comprehensive Guide to the ESG Strategy Simulation')
    r.font.size = Pt(14); r.italic = True
    spacer(doc)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Version 2.0 | 2026')
    r.font.size = Pt(12); r.font.color.rgb = TEAL
    page_break(doc)

    # ══════════════════ TABLE OF CONTENTS ══════════════════
    h(doc, 'Table of Contents', 1)
    toc = [
        'Part I: Getting Started',
        '  1. Welcome & Simulation Overview',
        '  2. Joining a Session & Onboarding',
        '  3. The Executive Cockpit',
        'Part II: The Game Loop',
        '  4. Decision-Making Framework',
        '  5. Round-by-Round Walkthrough (Rounds 1-10)',
        '  6. Strategic Pillars Paradigm',
        '  7. Round 10: Grand Finale & Ending Pathways',
        'Part III: Under the Hood',
        '  8. Mathematical Engines Explained',
        '  9. KPI Deep Dive',
        '  10. Scoring & Terminal Valuation',
        '  11. Flag Dependencies & Cascades',
        'Part IV: Reference',
        '  12. Strategic Tips & Common Mistakes',
        '  13. Glossary of Key Terms',
        '  14. Quick Reference Card',
        'Appendices',
        '  A. Decision Paradigm Comparison',
        '  B. Industry Vertical Profiles',
        '  C. Minigames & Side Activities',
    ]
    for item in toc:
        p = doc.add_paragraph(item)
        if not item.startswith('  '):
            for r in p.runs: r.bold = True
    page_break(doc)

    # ══════════════════ PART I HEADER ══════════════════
    t = h(doc, 'PART I: GETTING STARTED', 1, TEAL)
    page_break(doc)

    # ══════════════════ § 1: WELCOME ══════════════════
    h(doc, '1. Welcome & Simulation Overview', 1)
    body(doc, 'Welcome to Muressons Global Corporation — a multi-round ESG strategy simulation where you step into the role of Chief Sustainability Officer of a diversified multinational conglomerate.')
    body(doc, 'Your mission is to navigate 10 rounds (representing 5 years of corporate strategy) of escalating environmental, social, and governance crises while maximising the long-term Terminal Value of the corporation.')

    h(doc, '1.1 The Simulation Premise', 2)
    body(doc, 'Muressons Global Corporation is a diversified conglomerate with four business units, each facing unique ESG challenges. Every round presents a crisis scenario requiring strategic decisions that have cascading consequences across future rounds.')
    bullet(doc, 'Each round represents a 6-month semester of corporate strategy')
    bullet(doc, '10 rounds = 5 years of strategic decision-making')
    bullet(doc, 'Your objective: maximise Terminal Value (TV) = EBITDA × Exit Multiple × Regenerative Multiple')
    bullet(doc, 'Decisions are irreversible — once committed, your choices are permanently recorded')

    h(doc, '1.2 The Four Business Units', 2)
    body(doc, 'Your conglomerate comprises four distinct business units, each with different financial profiles and ESG exposures:')
    bu_headers = ['Business Unit', 'Revenue', 'OPEX', 'Key ESG Exposure']
    bu_rows = [
        ('💊 Muressons Pharma', '$18.0M', '$12.0M', 'High water dependency, clinical compliance'),
        ('⚡ Muressons Electronics', '$16.5M', '$11.5M', 'Highest carbon intensity (72), supply chain risk'),
        ('🛒 Muressons Consumer Goods', '$10.5M', '$7.5M', 'Packaging waste, consumer scrutiny'),
        ('💻 Muressons Software', '$8.5M', '$5.5M', 'Talent retention, AI ethics, lowest footprint'),
    ]
    styled_table(doc, bu_headers, bu_rows)
    spacer(doc)
    body(doc, 'Starting Financial Position: Corporate Treasury = $50.0M | Group Reputation = 50/100 | Synergy Multiplier = 1.00', bold=True)

    h(doc, '1.3 Difficulty Tiers', 2)
    styled_table(doc, ['Tier', 'Advanced Engines', 'Best For'],
        [('Standard', '8 core engines only', 'First-time players, introductory workshops'),
         ('Advanced', '8 core + 14 advanced engines', 'MBA students, experienced participants'),
         ('Expert', 'All engines + Regulatory Sandbox', 'Executive education, research sessions')])
    page_break(doc)

    # ══════════════════ § 2: JOINING ══════════════════
    h(doc, '2. Joining a Session & Onboarding', 1)
    h(doc, '2.1 Accessing the Simulation', 2)
    body(doc, 'Your facilitator will provide you with:')
    bullet(doc, 'A URL to access the simulation (e.g., https://muressons.example.com)')
    bullet(doc, 'An Executive Identifier (e.g., MUR-001) — your unique player ID')
    bullet(doc, 'A Clearance Cipher (password) — provided by the facilitator')

    login_img = os.path.join(IMG, 'login_screen.png')
    if os.path.exists(login_img):
        add_image(doc, login_img, caption='Figure 2.1 — Command Access Login Screen')
    spacer(doc)

    h(doc, '2.2 Starting a Solo Session', 2)
    body(doc, 'If you are practising individually, click "START SOLO SESSION" on the login screen. This creates a private session where you can explore the simulation at your own pace without needing facilitator credentials.')

    h(doc, '2.3 The Onboarding Tour', 2)
    body(doc, 'On your first login, an interactive 7-step tour guides you through the Executive Cockpit interface. Key stops include:')
    bullet(doc, 'Step 1: Welcome — Your role as Chief Sustainability Officer')
    bullet(doc, 'Step 2: KPI Dashboard — Understanding your key performance indicators')
    bullet(doc, 'Step 3: Investment Matrix — How to allocate capital across business units')
    bullet(doc, 'Step 4: Strategic Options — Navigating A/B/C crisis decisions')
    bullet(doc, 'Step 5: Market Ticker — Reading real-time market intelligence')
    bullet(doc, 'Step 6: Executive Mailbox — Crisis alerts and foreshadowing events')
    bullet(doc, 'Step 7: Commit Button — Submitting your final decisions')
    page_break(doc)

    # ══════════════════ § 3: EXECUTIVE COCKPIT ══════════════════
    h(doc, '3. The Executive Cockpit', 1)
    body(doc, 'The Executive Cockpit is your primary command interface throughout the simulation. Understanding its layout is essential for effective decision-making.')

    cockpit_img = os.path.join(IMG, 'cockpit.png')
    if os.path.exists(cockpit_img):
        add_image(doc, cockpit_img, caption='Figure 3.1 — The Executive Cockpit (Full View)')
    spacer(doc)

    h(doc, '3.1 Header Bar', 2)
    body(doc, 'The top bar displays critical status information:')
    bullet(doc, 'Round Indicator — Current round number (R1/10 to R10/10)')
    bullet(doc, 'Session Status — "LIVE" indicator with connection status')
    bullet(doc, 'Decision Paradigm Badge — Shows active paradigm (NARRATIVE, PILLARS, etc.)')
    bullet(doc, 'Logout Button — Exit the simulation (progress is saved)')

    h(doc, '3.2 KPI Gauges Panel (Left Sidebar)', 2)
    body(doc, 'The left panel shows your critical KPIs with tabs for KPIs, Charts, and Metrics:')
    styled_table(doc, ['KPI', 'Starting Value', 'What It Means'],
        [('💰 Treasury', '$50.0M', 'Your available cash for investments and operations'),
         ('🌿 Green Fund', '$0', 'Dedicated environmental investment fund'),
         ('🌟 Reputation', '50/100', 'Corporate reputation across all stakeholders'),
         ('🏭 Carbon', '2,635t', 'Total CO₂ emissions in tonnes'),
         ('📊 EBITDA', '$19.2M', 'Earnings before interest, taxes, depreciation & amortisation')])

    h(doc, '3.3 Investment Matrix', 2)
    inv_img = os.path.join(IMG, 'investment_matrix.png')
    if os.path.exists(inv_img):
        add_image(doc, inv_img, caption='Figure 3.2 — Investment Matrix with BU Sliders')
    body(doc, 'The Investment Matrix is where you allocate capital to each business unit:')
    bullet(doc, 'CSF Pool — Total available capital (Corporate Strategic Fund)')
    bullet(doc, 'Allocated — Amount currently distributed across BUs')
    bullet(doc, 'Remaining — Unallocated funds')
    bullet(doc, 'Per-BU Slider — Drag to set investment ratio (0% to 100%)')
    bullet(doc, 'BU Metrics — OPEX Base, Margin, Social License, Governance Risk per BU')

    h(doc, '3.4 Strategic Options Panel', 2)
    body(doc, 'Below the Investment Matrix, the Strategic Options panel presents the A/B/C crisis decision:')
    bullet(doc, 'Each option shows its title, description, and cost')
    bullet(doc, 'The Comparison Matrix below compares Treasury, Revenue, and Reputation impacts')
    bullet(doc, 'Select one option before committing — this choice is final')

    h(doc, '3.5 Bottom Navigation Bar', 2)
    body(doc, 'The bottom bar provides access to supplementary features:')
    styled_table(doc, ['Button', 'Function'],
        [('🎙️ Podcast', 'Listen to AI-generated round briefing audio'),
         ('📊 Leaderboard', 'View peer cohort performance rankings'),
         ('🏆 Badges', 'Track achievement badges earned'),
         ('🤖 Advisor', 'Consult the AI strategic advisor'),
         ('📈 Analytics', 'View detailed analytical dashboards'),
         ('📖 Glossary', 'Access the in-game glossary of terms'),
         ('🔊 Sound', 'Toggle sound effects and ambient audio'),
         ('🚪 Log Out', 'Exit the simulation')])

    h(doc, '3.6 Market Ticker', 2)
    body(doc, 'The scrolling ticker at the bottom displays real-time market data including ESG Index values, Carbon Credit prices, EU Taxonomy compliance percentages, Water Futures, Green Bond yields, and S&P Clean Energy metrics. These provide contextual market intelligence but do not directly affect gameplay.')
    page_break(doc)

    # ══════════════════ PART II HEADER ══════════════════
    t = h(doc, 'PART II: THE GAME LOOP', 1, TEAL)
    page_break(doc)

    # ══════════════════ § 4: DECISION FRAMEWORK ══════════════════
    h(doc, '4. Decision-Making Framework', 1)
    h(doc, '4.1 The Three-Step Decision Cycle', 2)
    body(doc, 'Every round follows a structured decision cycle:')

    body(doc, 'Step 1: REVIEW', bold=True)
    bullet(doc, 'Read the Intelligence Briefing — understand the crisis scenario and context')
    bullet(doc, 'Check the Executive Mailbox for market intelligence and foreshadowing events')
    bullet(doc, 'Review your current KPIs, treasury balance, and BU health metrics')
    bullet(doc, 'Complete any Pre-Requisite Gates (e.g., Stakeholder Map in R1)')

    body(doc, 'Step 2: DECIDE', bold=True)
    bullet(doc, 'Select one Strategic Option (A, B, or C) — read descriptions carefully')
    bullet(doc, 'Set Investment Matrix sliders for each BU — allocate your CSF pool')
    bullet(doc, 'Consider the Comparison Matrix to understand trade-offs between options')
    bullet(doc, 'Use the Confidence Nudge prompt to reflect before committing')

    body(doc, 'Step 3: COMMIT', bold=True)
    bullet(doc, 'Click the Commit button to submit your decisions')
    bullet(doc, 'Decisions are IRREVERSIBLE — the simulation uses immutable state recording')
    bullet(doc, 'After commit, review the Results Overlay showing KPI deltas and "What Changed"')
    bullet(doc, 'Check the Peer Leaderboard to see how you compare to other teams')

    h(doc, '4.2 Understanding the Investment Matrix', 2)
    body(doc, 'The CSF (Corporate Strategic Fund) is your total available CAPEX each round:')
    bullet(doc, 'CSF = Σ(Revenue - OPEX) - Dividends_Paid')
    bullet(doc, 'Each BU slider sets its Investment Ratio (0.0 to 1.0)')
    bullet(doc, 'CAPEX per BU = Investment Ratio × BU Revenue')
    bullet(doc, 'Total allocation cap: 120% of CSF (above 100% triggers a loan at 12% interest)')
    bullet(doc, 'Investment affects OPEX reduction via the Synergy Engine (see Section 8)')
    body(doc, 'Key Insight: Investments ≤ 10% apply immediately. Investments > 10% are DEFERRED one round (implementation lag). You pay now but benefit next round.', bold=True, italic=True)
    page_break(doc)

    # ══════════════════ § 5: ROUND WALKTHROUGH ══════════════════
    h(doc, '5. Round-by-Round Walkthrough', 1)
    body(doc, 'This section provides a detailed narrative walkthrough of all 10 rounds in the standard (Narrative Crisis) paradigm. Each round includes the crisis scenario, decision options, strategic considerations, and flag dependencies.')

    round_meta = {
        1: {'icon': '📋', 'theme': 'ESG Baseline Assessment', 'teach': 'Your R1 audit choice sets the "butterfly effect" — choosing a Surface Scan (Option A) sets the electronics_blindspot flag that DOUBLES crisis severity in Round 4.'},
        2: {'icon': '📊', 'theme': 'Double Materiality & Budget Allocation', 'teach': 'Option A (Materiality-Aligned Budget) sets the materiality_aligned flag worth +0.10 M_R at terminal valuation. This is the governance foundation.'},
        3: {'icon': '🌍', 'theme': 'Scope 3 Emissions & Supply Chain', 'teach': 'Beware the Marketing-Only Pledge (Option C) — it activates the Greenwashing Engine. If your average investment ratio drops below 15%, ALL BUs lose 8 Social Licence points.'},
        4: {'icon': '🔥', 'theme': 'Reputation Crisis & Contagion', 'teach': 'This is where R1 decisions cascade. If electronics_blindspot is active, crisis severity DOUBLES from 40 to 80. The Contagion Engine uses a sigmoid function to propagate damage.'},
        5: {'icon': '🌪️', 'theme': 'Physical Climate Risk', 'teach': 'The stochastic dice roll (75% chance of cyclone) makes this the first round where luck matters. But resilience investments from your choice determine damage absorption.'},
        6: {'icon': '🤖', 'theme': 'AI Ethics & Algorithmic Bias', 'teach': 'Option B (Ethical AI Overhaul at -$8M) earns the Truth Premium (+0.15 M_R). Option C (Monetise the Algorithm) triggers EU AI Act costs from R7 onward.'},
        7: {'icon': '♻️', 'theme': 'Circular Economy & Industrial Symbiosis', 'teach': 'The Synergy Unlock (Option C) is the single highest M_R bonus available (+0.30). If synergy_multiplier ≥ 0.80, this is the most valuable single decision in the game.'},
        8: {'icon': '💧', 'theme': 'Water Scarcity & Blue Stress', 'teach': 'Water-dependent BUs (Pharma at 85%) face severe revenue cuts. Choosing to prioritise Electronics water (Option B) BLOCKS the +0.20 Resilience M_R bonus.'},
        9: {'icon': '⚖️', 'theme': 'Just Transition & Workforce Justice', 'teach': 'Option C (Community Fund) earns +0.18 M_R with Just Transition scaling. Option A (Immediate Closure) triggers the Strike Probability Engine — a stochastic revenue-zeroing event.'},
        10: {'icon': '🏛️', 'theme': 'Grand Finale — Activist Ultimatum', 'teach': 'All accumulated flags are evaluated. The Regenerative Multiple (M_R) is calculated, Terminal Value is computed, and your Corporate Archetype is revealed.'},
    }

    for r in range(1, 11):
        rc = ROUND_CONFIGS.get(r, {})
        meta = round_meta.get(r, {})
        crisis = rc.get('crisis', {})
        options = rc.get('options', {})

        h(doc, f"Round {r}: {meta.get('icon','')} {rc.get('title', '')} — {rc.get('theme', meta.get('theme',''))}", 2)
        if crisis.get('description'):
            body(doc, f"Crisis Scenario: {crisis.get('icon','')} {crisis.get('title','')}", bold=True)
            body(doc, crisis['description'])

        if options:
            body(doc, 'Decision Options:', bold=True)
            option_table(doc, options)
            # Flag summary
            for okey in sorted(options.keys()):
                opt = options[okey]
                flags = opt.get('flags_set', [])
                if flags:
                    bullet(doc, f"Flags: {', '.join(flags)}", bold_prefix=f"Option {opt.get('label', okey[-1].upper())}: ")

        if meta.get('teach'):
            body(doc, '📚 Teaching Point:', bold=True)
            body(doc, meta['teach'], italic=True)
        spacer(doc)
    page_break(doc)

    # ══════════════════ § 6: STRATEGIC PILLARS ══════════════════
    h(doc, '6. Strategic Pillars Paradigm', 1)
    body(doc, 'In the Strategic Pillars paradigm (multi_toggles), instead of choosing a single A/B/C option, you make decisions across five strategic areas simultaneously: Energy, Operations, Supply Chain, Offsetting, and Human Resources. Each area offers three options with different costs and impacts.')

    for r in range(1, min(6, max(PILLAR_OPTIONS.keys()) + 1)):
        po = PILLAR_OPTIONS.get(r, {})
        if not po:
            continue
        h(doc, f"Round {r}: {po.get('title', '')}", 2)
        body(doc, po.get('description', ''))
        areas = po.get('areas', {})
        for area_key, area_data in areas.items():
            body(doc, f"{area_data.get('icon', '')} {area_data.get('label', area_key.title())}", bold=True)
            opts = area_data.get('options', {})
            if opts:
                headers = ['Option', 'Cost', 'Key Impacts']
                rows = []
                for ok, ov in opts.items():
                    cost = ov.get('cost', 0)
                    cost_str = f"${abs(cost)/1_000_000:.1f}M" if abs(cost) >= 1_000_000 else f"${cost:,}" if cost != 0 else 'Free'
                    if cost > 0: cost_str = f"+{cost_str}"
                    elif cost < 0: cost_str = f"-{cost_str.lstrip('-')}"
                    imps = ov.get('impacts', {})
                    imp_str = ', '.join(f"{k}: {'+' if v > 0 else ''}{v}" for k, v in imps.items() if isinstance(v, (int, float))) or 'None'
                    rows.append((ov.get('title', ok), cost_str, imp_str))
                styled_table(doc, headers, rows)
            spacer(doc)
    page_break(doc)

    # ══════════════════ § 7: GRAND FINALE ══════════════════
    h(doc, '7. Round 10: Grand Finale & Ending Pathways', 1)
    h(doc, '7.1 The Five Ending Pathways', 2)
    body(doc, 'The simulation features five dynamic R10 crisis scenarios. The facilitator selects the ending pathway at session creation. Players receive subtle foreshadowing hints during Rounds 5-8 but never see the pathway name directly.')

    for pw_id, pw_desc in PATHWAY_DESCRIPTIONS.items():
        h(doc, f"🎯 {pw_desc['name']}", 3)
        body(doc, pw_desc['description'])
        fw = FORESHADOWING.get(pw_id, {})
        if fw:
            body(doc, 'Foreshadowing Events:', bold=True)
            for rnd, events in sorted(fw.items()):
                for evt in events:
                    bullet(doc, f"R{rnd}: {evt.get('headline', '')}")
        cfg = PATHWAY_R10_CONFIGS.get(pw_id, {})
        if cfg:
            opts = cfg.get('options', {})
            if opts:
                body(doc, 'R10 Decision Options:', bold=True)
                option_table(doc, opts)
        spacer(doc)

    h(doc, '7.2 Corporate Archetypes', 2)
    body(doc, 'Your final M_R score determines your Corporate Archetype:')
    styled_table(doc, ['Archetype', 'M_R Threshold', 'Description'],
        [('🌱 Regenerative Titan', '≥ 1.80', 'Gold standard — rebuilt natural capital with superior financial returns'),
         ('🏦 De-risked Safe Haven', '≥ 1.20', 'Avoided tail risks but innovation may be stalling'),
         ('⚠️ Fragile Giant', '≥ 0.80', 'Financially viable but structurally brittle — vulnerable to future shocks'),
         ('💀 Stranded Relic', '< 0.80', 'Structural decline — chronic underinvestment in sustainability'),
         ('🔧 Turnaround Manager', 'Survival Mode', 'Entered crisis stabilisation — emergency measures activated')])

    arch_img = os.path.join(IMG, 'archetypes.png')
    if os.path.exists(arch_img):
        add_image(doc, arch_img, caption='Figure 7.1 — Corporate Archetype Profiles')

    h(doc, '7.3 Game Over Summary', 2)
    body(doc, 'After Round 10, the simulation presents:')
    bullet(doc, 'Terminal Value — Your final corporation valuation')
    bullet(doc, 'Regenerative Multiple (M_R) — Your sustainability-adjusted multiplier')
    bullet(doc, 'Corporate Archetype — Your strategic profile classification')
    bullet(doc, 'Peer Leaderboard — How you rank against other teams')
    bullet(doc, 'Balanced Scorecard — Detailed analysis across three tabs (Scorecard/Analysis/Rounds)')

    sc_img = os.path.join(IMG, 'scorecard.png')
    if os.path.exists(sc_img):
        add_image(doc, sc_img, caption='Figure 7.2 — Balanced Scorecard Analysis')
    page_break(doc)

    return doc
