"""Part 4: Dashboard Guides, Pitfalls, Planning, Assessment, FAQ, Appendices."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from docx_styles import *

def build_dashboard_guide(doc):
    add_page_break(doc)
    doc.add_heading('PART 4 — DASHBOARD GUIDES, PLANNING & APPENDICES', level=1)
    doc.add_heading(u'§10A. Facilitator Dashboard Visual Guide', level=1)
    doc.add_paragraph('This section documents every tool available in the Facilitator Dashboard with screenshots and usage guidance.')

    doc.add_heading('10A.1 Command Center', level=2)
    add_screenshot_placeholder(doc, 'Dashboard Home — summary cards, alert panels, round briefing card')
    add_styled_table(doc, ['Tool', 'Icon', 'Purpose', 'When to Use'],
        [['Dashboard Home', u'🏠', 'At-a-glance: active cohorts, players, avg round, KPI alerts (lagging, low treasury, low rep). Quick-action buttons. Current round Teleprompter card.', 'Start of every session. First screen after login.'],
         ['Round Timeline', u'📅', 'Visual timeline of round progression. Quiz difficulty controls (easy/medium/hard). Interview control panel.', 'Check pacing. Toggle quizzes.'],
         ['Teleprompter', u'🎤', 'Full-screen presenter mode: talking points, engines likely to fire, discussion prompts, key themes.', 'Before delivering each round briefing.'],
         ['Leaderboard', u'🏆', 'Ranked matrix: Treasury, Rep, Synergy, EBITDA, round, terminal value. Sortable. Delete/reset per session.', 'Monitor competition. Identify struggling teams.']])
    add_screenshot_placeholder(doc, 'Teleprompter in full-screen presenter mode')
    add_screenshot_placeholder(doc, 'Leaderboard matrix with sortable columns')

    doc.add_heading('10A.2 Live Classroom', level=2)
    add_styled_table(doc, ['Tool', 'Icon', 'Purpose', 'When to Use'],
        [['Player Registry', u'📋', 'All enrolled players: session IDs, cohort, names, timestamps, connection status.', 'Verify enrolment. Check connections.'],
         ['Session Viewer', u'👁️', 'Deep-dive: full KPI breakdown, round history, decisions, real-time state.', 'Investigate specific team.'],
         ['Team Impersonation', u'🎭', 'View cockpit exactly as player sees it — dashboard, mailbox, decisions, KPIs.', 'Live debugging, demos, walkthroughs.'],
         ['Swipe File / Inbox', u'📬', 'Send pre-written or custom messages to individual teams. Appears in mailbox.', 'Inject narrative, board directives, alerts.'],
         ['Bulk Messaging', u'📢', 'Announcements to all or selected cohorts. Templates + custom.', 'Class-wide announcements.'],
         [u'Manual Overrides ⭐', u'⚡', 'Directly modify KPIs or force-advance rounds.', 'Live interventions, error correction.'],
         [u'Interventions ⭐', u'🎮', 'Configure available interventions per cohort.', 'Pre-session toolkit setup.']])
    add_screenshot_placeholder(doc, 'Player Registry with connection status indicators')
    add_screenshot_placeholder(doc, 'Team Impersonation showing student cockpit view')

    doc.add_heading('10A.3 Analytics & Assessment', level=2)
    add_styled_table(doc, ['Tool', 'Icon', 'Purpose', 'When to Use'],
        [['Cohort Analytics', u'📈', '6-tab suite: Decision Heatmap, Time-to-Decision, Cohort Comparison, Convergence, Learning Outcomes, Risk Exposure.', 'Pattern recognition across cohorts.'],
         ['Cohort Comparison', u'📊', 'Side-by-side KPI trajectory charts. Toggle: Treasury, Rep, Synergy, EBITDA.', 'Inter-cohort debrief.'],
         ['Complexity Feed', u'📡', 'Real-time feed: engine triggers, narrative injections, math outputs.', 'Monitor hidden engines.'],
         ['Decision History', u'🕰️', 'Chronological audit: timestamps, choices, CapEx, KPI deltas. Filterable.', 'Post-round analysis, grading.'],
         ['DNA Comparison', u'🧬', 'Consequence DNA Sankey across cohorts. Causal chain divergence.', 'R10 debrief: why paths diverged.'],
         ['Round Debrief', u'📝', 'Per-round summary: decisions, outcomes, outliers, discussion points.', 'Structured post-round discussion.'],
         ['Scorecard Sandbox', u'🧲', 'Interactive TBL scorecard whiteboard. Teaching tool only.', 'Demonstrate scoring math.'],
         ['Student Bonuses', u'🎁', 'Manual bonuses: participation, presentation, custom points.', 'Reward performance.'],
         ['Peer Evaluations', u'🔄', 'Anonymous peer ratings: collaboration, contribution, communication.', 'Teamwork assessment.'],
         ['Export Reports', u'📤', 'CSV/PDF: sessions, leaderboard, decisions, analytics, grading sheets.', 'End of simulation.']])
    add_screenshot_placeholder(doc, 'Cohort Analytics — Decision Heatmap tab')

    doc.add_heading('10A.4 Configuration', level=2)
    add_styled_table(doc, ['Tool', 'Icon', 'Purpose', 'When to Use'],
        [[u'Auto-Pause ⭐', u'⏸️', 'Automatic pause conditions: low treasury, rep floor, bankruptcy, custom KPI.', 'Pre-session safety net.'],
         [u'Undo Round ⭐', u'↩️', 'Roll back last round, restore all KPIs.', 'Error correction, teaching moment replay.'],
         [u'Regulatory Sandbox ⭐', u'⚖️', 'Inject Pigou taxes, Coase bargaining, Ostrom instruments.', 'Advanced: systemic resilience testing.'],
         [u'Materiality Matrix ⭐', u'🧩', "Mendelow's drag-and-drop. Lead: customize. Base: read-only.", 'Configure materiality framework.'],
         ['Teaching Journal', u'📝', 'Private notes + timestamped annotations. Persisted.', 'Ongoing observations, debrief prep.'],
         ['Technical Reference', u'📐', 'In-app reference: terminology, engines, formulas, scorecard.', 'Quick look-up during gameplay.'],
         [u'Activity Logs ⭐', u'📋', 'Audit log + session management (delete, hard-reset).', 'Post-session cleanup.']])
    doc.add_paragraph(u'⭐ = Requires Lead Facilitator or Super Admin role')

def build_god_mode_guide(doc):
    add_page_break(doc)
    doc.add_heading(u'§10B. God Mode Dashboard Visual Guide', level=1)
    doc.add_paragraph('The Super Administrator console provides system-wide control.')
    add_screenshot_placeholder(doc, 'God Mode System Overview with scaffolding toggles')
    
    categories = [
        ('Command Center', [['System Overview', 'Unified dashboard, session health, scaffolding toggles'],
                            ['Platform Analytics', 'Aggregated stats across ALL facilitators'],
                            ['Activity & Complexity', 'Immutable audit trail + live firehose']]),
        ('Cohort Orchestration', [['Facilitator Registry', 'Create/edit facilitators, roles, permissions, cohort limits'],
                                   ['Cohort Provisioning', 'Provision sessions, assign facilitators, paradigms'],
                                   ['Session Controls', 'Pacing, broadcasts, visibility, scheduling'],
                                   ['Team Interventions', 'Inject capital, penalties, narrative events'],
                                   ['Crisis Overrides', 'Activate crises, Black Swans, end-game pathways']]),
        ('Engine Configuration', [['Macro Economics', 'Global baselines, scenario presets, master variables'],
                                   ['Systemic Risk', 'Black Swans, NPC cascades, tipping points, foreshadowing'],
                                   ['Profile Archetypes', 'M_R thresholds for archetype classification'],
                                   ['Regulatory Sandbox', 'Pigou taxes, Coase bargaining, Ostrom governance']]),
        ('Danger Zone', [['Backup & Export', 'Full simulation snapshots'],
                          ['Factory Reset', 'Hard wipe ALL databases — typed confirmation required']]),
    ]
    for cat_name, tools in categories:
        doc.add_heading(cat_name, level=2)
        add_styled_table(doc, ['Tool', 'Purpose'], tools)

def build_pitfalls(doc):
    add_page_break(doc)
    doc.add_heading(u'§11. Common Student Pitfalls & Teaching Moments', level=1)
    pitfalls = [
        ('"Option A is always best"', 'The shuffle engine randomises option order per session. No positional bias exists. Teach: read content, not position.'),
        ('"Skip the audit, save $3M"', 'R1 Surface Scan costs $15M+ at R4 via contagion sigmoid. NPV of audit = 5x cost. Teach: option value of information.'),
        ('"HR is optional"', 'Burnout follows quadratic curve. 60% burnout = 36% OPEX penalty + 66% R9 strike risk. Teach: human capital as binding constraint.'),
        ('"ESG is a cost centre"', 'Terminal value spread: Titan $230M vs. Relic -$7M = 675% ROI on ESG investment. Teach: ESG as value driver.'),
        ('"Ignore stakeholders"', 'Autonomous agents cascade: Journalist → Activist → Regulator. 3-agent hostile = corporate collapse. Teach: stakeholder salience.'),
        ('"NCD doesn\'t matter"', '6% compounding: NCD 200 → 301 in 7 rounds. Deducted from terminal value. Teach: ecological debt accumulation.'),
        ('"I can recover in R9-R10"', 'Most M_R gates close by R8. early_decarboniser (R3), materiality_aligned (R2), nature_based (R5) — all irreversible. Teach: path dependency.'),
        ('"Diversify everything equally"', 'Synergy rewards concentration (√ scaling). Spreading $15M across 3 pillars equally yields less than focused investment. Teach: diminishing returns.'),
        ('"Deny and deflect is free"', 'Governance risk compounds through Cash Conversion drag, reducing revenue efficiency every round. Teach: hidden costs of opacity.'),
    ]
    for title, text in pitfalls:
        doc.add_heading(title, level=3)
        doc.add_paragraph(text)

def build_planning(doc):
    add_page_break(doc)
    doc.add_heading(u'§13. Session Planning & Logistics', level=1)
    doc.add_heading('13.1 Time Allocation', level=2)
    add_styled_table(doc, ['Phase', 'Duration', 'Activity'],
        [['Setup', '10 min', 'Server check, player registration, cohort creation'],
         ['Round Briefing', '5 min/round', 'Facilitator delivers teleprompter script'],
         ['Decision Phase', '3-5 min/round', 'Teams discuss and submit decisions'],
         ['Engine Resolution', '1 min/round', 'System processes tick, results appear'],
         ['Debrief', '5 min/round', 'Post-round discussion using prompts'],
         ['R5 Checkpoint', '15 min', 'Shadow Board Audit + mid-game formative'],
         ['R10 Capstone', '20 min', 'Terminal valuation reveal + Thiagarajan debrief'],
         ['TOTAL', '~130-150 min', 'Full 10-round session']])
    
    doc.add_heading('13.2 Multi-Session Format', level=2)
    add_styled_table(doc, ['Session', 'Rounds', 'Duration', 'Focus'],
        [['Session 1', 'R1-R5', '75 min', 'Foundation + Crisis + Shadow Board midpoint'],
         ['Session 2', 'R6-R10', '75 min', 'Integration + Finale + Capstone debrief']])
    
    doc.add_heading('13.3 Pre-Session Checklist', level=2)
    add_bullet_list(doc, [
        'Server running and accessible (verify with /api/health endpoint)',
        'Cohort created with correct industry verticals and experience level',
        'Player registration links distributed (share cohort join code)',
        'Side tracks assigned if applicable',
        'Ending pathway selected (or left on auto-detect)',
        'Pedagogical toggles configured (prediction gates, timer, peer learning)',
        'Teleprompter scripts reviewed for current round',
    ])

def build_assessment(doc):
    add_page_break(doc)
    doc.add_heading(u'§14. Assessment & Grading Rubric', level=1)
    add_styled_table(doc, ['Component', 'Weight', 'Assessment Method'],
        [['Participation & Engagement', '20%', 'Attendance, decision submission timeliness, Board Room Moment completion'],
         ['Reflective Quality', '40%', 'Strategy memo depth (R5), prediction calibration, mental model shift R1→R10'],
         ['Terminal Outcome', '20%', 'M_R score and archetype classification (quantitative)'],
         ['Peer Debrief', '20%', 'Cross-team analysis quality, theory application, transferable insights']])
    
    doc.add_heading('14.1 Reflective Journal Prompts', level=2)
    add_styled_table(doc, ['Round', 'Prompt'],
        [['R1', 'What information would change your audit decision? What is the value of knowing?'],
         ['R4', 'Map the causal chain from R1 to R4. What assumption broke?'],
         ['R5', 'How did the Shadow Board change your perspective? Which persona was hardest to hear?'],
         ['R7', 'How did your HR investment history affect R7 outcomes? What is workforce readiness worth?'],
         ['R10', 'Compare your R1 mental model to R10. What shifted? What framework explains the change?']])

def build_faq(doc):
    add_page_break(doc)
    doc.add_heading(u'§15. Facilitator FAQ', level=1)
    faqs = [
        ('What if a team goes bankrupt?', 'The Turnaround Arc activates automatically when treasury hits negative. Phase 1 (Crisis): Emergency Restructuring option appears — divest worst BU at 60% book value, -15% OPEX haircut. Phase 2 (Stabilisation): Reduced option set with recovery focus. Teams can recover to Fragile Giant but rarely reach Titan.'),
        ('What if students game the system?', 'Three anti-gaming mechanisms: (1) Option Shuffle Engine randomises A/B/C order per session; (2) Stochastic elements (cyclone 75%, whistleblower 40%) prevent deterministic optimisation; (3) Pillar mutual exclusivity prevents maxing all sliders.'),
        ('Can I run without side tracks?', 'Yes. Side tracks are optional enrichment. The core 10-round loop is fully self-contained. Side tracks add depth but are not required for pedagogical objectives.'),
        ('How to handle uneven performance?', 'Use God Mode real-time balancing: inject capital to struggling teams, increase carbon tax for leaders, trigger custom Black Swans. Auto-Pause triggers can halt advanced teams while others catch up.'),
        ('What if the server crashes mid-round?', 'All state is persisted to PostgreSQL after every tick. On restart, sessions resume from their last completed round. Player connections auto-reconnect via WebSocket.'),
        ('Can I modify round configurations?', 'Yes, via decision_overrides.json — a JSON overlay that merges with ROUND_CONFIGS at runtime. Changes take effect immediately without server restart. Back up the file before editing.'),
        ('How to explain math to non-quant students?', 'Use the Scorecard Sandbox (§10A.3) — interactive whiteboard where sliders show how weights affect terminal value. Focus on directional relationships (more burnout = higher cost), not formulas.'),
    ]
    for q, a in faqs:
        doc.add_heading(q, level=3)
        doc.add_paragraph(a)

def build_appendix_a(doc):
    add_page_break(doc)
    doc.add_heading('Appendix A: Glossary of Definitions', level=1)
    terms = [
        ('EBITDA', 'Earnings Before Interest, Taxes, Depreciation, and Amortisation. Sum of (Revenue - OPEX) across all BUs.'),
        ('Terminal Value (TV)', 'The company\'s projected worth at Year 5. Calculated as (EBITDA - Carbon Cost) x Exit Multiple x M_R.'),
        ('Regenerative Multiple (M_R)', 'Additive multiplier (1.0-2.1) rewarding sustainable strategy. Built from 10+ flag-based bonuses across R1-R10.'),
        ('Carbon Intensity (CI)', 'Per-BU metric (0-100) measuring carbon emissions per unit of output. Higher = worse.'),
        ('Natural Capital Debt (NCD)', 'Ecological liability that compounds at 6%/round. Deducted from terminal value.'),
        ('Social License to Operate (SLO)', 'Community acceptance score (0-100). Below 75 triggers -0.40 M_R instability discount.'),
        ('Governance Risk Score', 'Per-BU metric (0-100) measuring governance quality. Higher = worse. Feeds Cash Conversion drag.'),
        ('Synergy Multiplier', 'Cross-BU integration score (0-2.0). Gates R10 Option A (requires >80). Affects terminal value.'),
        ('Workforce Readiness', 'Global metric (0-100) measuring workforce adaptability. Gates R7 circular economy returns.'),
        ('Contagion', 'Sigmoid-based reputation damage propagation engine. Severity doubled by blindspot flags.'),
        ('VRIO Advantage', 'Competitive advantage score (0.50-1.00). Decays 5%/round without investment.'),
        ('Burnout Index', 'Per-BU metric (0-100). Quadratic OPEX penalty. >60% triggers R9 strike risk.'),
        ('Brain-Drain', 'Software BU talent penalty when reputation <40. -15% revenue/round.'),
        ('Fog of War', 'Progressive engine disclosure. R1-R3: 5 engines visible. R8+: all visible.'),
        ('Shadow Board Audit', 'Mandatory R5 interception. 3 persona evaluations. Rejections set R10 pathway flags.'),
        ('Ending Pathway', 'One of 5 R10 crisis scenarios determined by R5 flags and KPI thresholds.'),
        ('Turnaround Arc', 'Emergency mode activated when treasury goes negative. Option T injected.'),
        ('Pillar Mode', 'Budget allocation variant where $15M is distributed across 3 mutually exclusive pillars.'),
        ('Foreshadowing', 'Planted news items in Market Feed (R5-R8) that signal the upcoming R10 pathway.'),
        ('God Mode', 'Super Administrator console for system-wide control over all simulation parameters.'),
        ('CSRD', 'Corporate Sustainability Reporting Directive (EU). Mandates double materiality assessment.'),
        ('ESRS', 'European Sustainability Reporting Standards. CSRD implementation standards.'),
        ('TCFD', 'Task Force on Climate-related Financial Disclosures. Physical/transition risk framework.'),
        ('TNFD', 'Taskforce on Nature-related Financial Disclosures. Biodiversity risk framework.'),
    ]
    for term, defn in terms:
        p = doc.add_paragraph()
        r = p.add_run(term + ': ')
        r.font.bold = True; r.font.size = Pt(10)
        r2 = p.add_run(defn)
        r2.font.size = Pt(10)

def build_appendix_b(doc):
    add_page_break(doc)
    doc.add_heading('Appendix B: Complete Engine Variable Registry', level=1)
    
    doc.add_heading('B.1 Global State Variables', level=2)
    add_styled_table(doc, ['Variable', 'Initial', 'Range', 'Unit', 'Modified By'],
        [['corporate_treasury', '50,000,000', '0-∞', '$', 'All options, engine penalties'],
         ['group_reputation', '55.0', '0-100', 'pts', 'Contagion, options, agents'],
         ['synergy_multiplier', '1.00', '0-2.0', 'x', 'Synergy engine, R7 options'],
         ['workforce_readiness', '50.0', '0-100', 'pts', 'HR investment, burnout inverse'],
         ['inflation_index', '1.00', '1.0-1.5', 'x', '+2-3%/round cumulative'],
         ['green_transition_fund', '0', '0-∞', '$', 'Green Bond, R7 circular'],
         ['dividend_ratchet', '0', '0-∞', '$', 'Board governance minigame']])
    
    doc.add_heading('B.2 Per-BU State Variables', level=2)
    add_styled_table(doc, ['Variable', 'Pharma', 'Electronics', 'CG', 'Software', 'Range'],
        [['revenue_base', '18M', '16.5M', '10.5M', '8.5M', '0-∞'],
         ['opex_base', '12M', '11.5M', '7.5M', '5.5M', '0-∞'],
         ['carbon_intensity', '35', '72', '48', '12', '0-100'],
         ['water_dependency', '82', '58', '65', '12', '0-100'],
         ['natural_capital_debt', '120', '200', '150', '30', '0-∞'],
         ['social_license_score', '50', '50', '50', '50', '0-100'],
         ['governance_risk_score', '15', '20', '10', '25', '0-100'],
         ['staff_burnout_index', '10', '10', '10', '10', '0-100'],
         ['vrio_advantage', '0.80', '0.80', '0.80', '0.80', '0.5-1.0']])
    
    doc.add_heading('B.4 Flag Registry', level=2)
    add_styled_table(doc, ['Flag', 'Set By', 'Downstream Effect'],
        [['electronics_blindspot', 'R1 Opt A', '2x R4 severity (40→80)'],
         ['deep_audit_completed', 'R1 Opt B', 'R4 severity stays at 40'],
         ['materiality_aligned', 'R2 Opt A', '+0.10 M_R; NCD forgiveness 25%'],
         ['materiality_ignored', 'R2 Opt C', '40% budget clawback; Green Bond blocked'],
         ['early_decarboniser', 'R3 Opt A', '+0.15 M_R; R7 amplification'],
         ['green_bond_active', 'R3 Opt B', '-15 NCD over 3 rounds'],
         ['remediation_active', 'R4 Opt A', '+0.10 M_R'],
         ['nature_based_resilience', 'R5 Opt B', '+0.20 M_R (Resilience Champion)'],
         ['insurance_only', 'R5 Opt C', 'BLOCKS +0.20 M_R permanently'],
         ['ethical_ai_overhaul', 'R6 Opt B', '+0.15 M_R (Truth Premium)'],
         ['ai_monetised', 'R6 Opt A', 'Contagion spike; -20 rep'],
         ['waste_to_energy', 'R7 Opt C', '+0.30 M_R; synergy unlock'],
         ['managed_transition', 'R9 Opt B', '+0.12 M_R'],
         ['community_fund', 'R9 Opt C', '+0.18 M_R'],
         ['shareholder_alienated', 'R5 Shadow Board', 'Activates Activist pathway'],
         ['community_distrust', 'R5 Shadow Board', 'Activates Community pathway'],
         ['scientist_dismissed', 'R5 Shadow Board', 'Activates Climate pathway']])

def build_appendix_c(doc):
    add_page_break(doc)
    doc.add_heading('Appendix C: Academic Reference Matrix', level=1)
    doc.add_paragraph('Complete mapping of every cited theory to its simulation application, organized by round.')
    
    refs = [
        ['Mendelow, A. (1991)', 'Stakeholder Mapping', 'R1', 'Drag-and-drop Power x Interest matrix classifies 8 stakeholders before audit decision.', 'What stakeholder did you misclassify? How would reclassification change your strategy?'],
        ['Mitchell, R., Agle, B., & Wood, D. (1997)', 'Stakeholder Salience', 'R1,R5,R9', 'Power x Legitimacy x Urgency drives autonomous agent escalation levels and Shadow Board persona authority.', 'Which stakeholder gained urgency during the simulation? Why?'],
        ['EU Commission (2022)', 'CSRD / ESRS', 'R2', 'CFO materiality gate requires double materiality classification. ESRS 1 §1.51 violation triggers 40% clawback.', 'How does mandatory vs. voluntary disclosure change behaviour?'],
        ['Dixit, A. & Pindyck, R. (1994)', 'Real Options Theory', 'R1→R4', 'Deep audit = purchasing an option on future crisis mitigation. Option NPV = 5x cost ($3M → $15M avoided).', 'What was the option value of the R1 audit?'],
        ['Argyris, C. (1977)', 'Double-Loop Learning', 'R4', 'R4 cascade forces players to question R1 assumptions — the core double-loop trigger.', 'What assumption broke at R4? How did you update your mental model?'],
        ['Kahneman, D. (2011)', 'System 1/2 Thinking', 'R4,R6', 'Time pressure and stochastic elements force heuristic (System 1) decisions. Debrief reveals analytical (System 2) gaps.', 'Did time pressure change your decision? How?'],
        ['Moon, J. (2004)', 'Reflection Protocol', 'R4,R5', '3-stage Board Room Moments: Noticing → Making Sense → Working with Meaning.', 'What surprised you? Why? What will you change?'],
        ['Jensen, M. & Meckling, W. (1976)', 'Agency Theory', 'R5', 'Shadow Board personas embody principal-agent conflicts: shareholder value vs. community welfare vs. scientific evidence.', 'Whose interests did you prioritise? Why?'],
        ['Barney, J. (1991)', 'Resource-Based View', 'R7', 'VRIO advantage decays without investment. Circular capabilities = rare, valuable, non-substitutable.', 'Which capability is your most durable competitive advantage?'],
        ['Teece, D. (2007)', 'Dynamic Capabilities', 'R7', 'Workforce readiness gates circular economy returns. Sensing, seizing, reconfiguring capabilities.', 'How did workforce readiness constrain your options?'],
        ['Hardin, G. (1968)', 'Tragedy of the Commons', 'R8', 'Water scarcity forces collective resource allocation. Prioritising one BU depletes shared resource.', 'Is prioritising highest-margin BU rational? From whose perspective?'],
        ['Rawls, J. (1971)', 'Justice as Fairness', 'R9', 'Difference Principle applied: factory closure must benefit the least advantaged (workers/community).', 'Who bears the cost of decarbonisation? Is that just?'],
        ['Freeman, R.E. (1984)', 'Stakeholder Theory', 'R9', 'Community Fund option embodies stakeholder value creation beyond shareholder returns.', 'Does stakeholder investment create or destroy shareholder value?'],
        ['Costanza, R. et al. (1997)', 'Natural Capital', 'All', 'NCD compounds at 6%/round modelling ecological debt. Deducted from terminal value as liability.', 'What is the interest rate on ecological debt?'],
        ['Meadows, D. (1999)', 'Leverage Points', 'R10', 'Debrief overlay identifies 12 leverage points in the simulation system hierarchy.', 'Where would you intervene in this system? At what leverage point?'],
        ['Kolb, D. (1984)', 'Experiential Learning', 'All', 'Full cycle: R1-R5 (Concrete Experience) → R4 debrief (Reflection) → R6-R8 (Conceptualisation) → R9-R10 (Experimentation).', 'How did your strategy evolve across the learning cycle?'],
        ['Thiagarajan, S. (1993)', 'Debrief Protocol', 'R10', '3-phase: How Do You Feel? (2 min) → What Happened? (5 min) → So What? (10 min).', 'What one principle would you take to a real boardroom?'],
    ]
    add_styled_table(doc, ['Citation', 'Framework', 'Round(s)', 'How Applied in Simulation', 'Debrief Prompt'], refs, col_widths=[1.5, 1.0, 0.5, 2.5, 2.0])
