"""
Append Section 16: Regulatory Sandbox Controller — Middleware Intercept Architecture
to the Muressons Simulation Briefings (ver 9 → ver 10).

This section documents the Expert-Tier regulatory sandbox middleware that
intercepts the simulation state-transition loop, applying exogenous policy shocks
based on Pigou, Coase, and Ostrom frameworks.
"""
import docx
import os
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT


def add_formula(doc, formula_text):
    """Add a monospaced formula block."""
    p = doc.add_paragraph()
    run = p.add_run(formula_text)
    run.font.name = 'Courier New'
    run.font.size = Pt(10)
    return p


def add_theory_citation(doc, text):
    """Add an italicised academic citation."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    return p


def append_regulatory_sandbox_section():
    base_dir = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim"
    source_doc = os.path.join(base_dir, "Muressons_Simulation_Briefings ver 9.docx")

    if not os.path.exists(source_doc):
        print(f"File not found: {source_doc}")
        return

    doc = docx.Document(source_doc)

    # ═══════════════════════════════════════════════════════════
    #  SECTION 16: REGULATORY SANDBOX CONTROLLER
    # ═══════════════════════════════════════════════════════════
    doc.add_page_break()
    doc.add_heading(
        'Section 16: Regulatory Sandbox Controller — '
        'Middleware Intercept & Exogenous Policy Shocks',
        level=1,
    )

    # ── 16.0 Overview ────────────────────────────────────────
    doc.add_paragraph(
        "The Regulatory Sandbox Controller (SE-7) is the expert-tier capstone module of the "
        "Muressons simulation. It intercepts the standard state-transition pipeline before values "
        "are finalized in the global_state dictionary, injecting exogenous policy shocks that force "
        "players to confront sudden, asymmetric regulatory interventions. This section serves as the "
        "comprehensive facilitator reference for deploying, calibrating, and debriefing sandbox "
        "scenarios in expert-tier classroom sessions."
    )

    # ── 16.1 Pedagogical Rationale ───────────────────────────
    doc.add_heading('16.1 Pedagogical Rationale', level=2)
    doc.add_paragraph(
        "Standard rounds test internal corporate decision-making — capital allocation, stakeholder "
        "trade-offs, and value creation. The Regulatory Sandbox shifts the pedagogical frame to "
        "macroeconomic policy design, asking: 'What happens when the rules of the game change mid-play?' "
        "This simulates the real-world experience of ESG regulatory disruption, where new carbon pricing "
        "mechanisms, due diligence mandates, or water-rights litigation can invalidate existing strategies "
        "overnight."
    )
    doc.add_paragraph(
        "The module is designed exclusively for expert-tier cohorts (e.g., MBA programmes, executive "
        "education, policy master's courses) where participants have sufficient grounding in environmental "
        "economics to engage critically with the theoretical frameworks being modelled."
    )

    # ── 16.2 Theoretical Foundations ─────────────────────────
    doc.add_heading('16.2 Theoretical Foundations', level=2)

    doc.add_heading('16.2.1 Pigouvian Taxation (Pigou, 1920)', level=3)
    doc.add_paragraph(
        "Arthur Cecil Pigou's foundational insight: negative externalities (pollution, carbon emissions, "
        "biodiversity loss) represent a market failure that can be corrected by imposing direct levies on "
        "'bads'. In the simulation, this manifests as a per-BU carbon tax calculated against each unit's "
        "absolute carbon footprint."
    )
    add_theory_citation(
        doc,
        "Pigou, A. C. (1920). The Economics of Welfare. London: Macmillan. "
        "— The tax forces firms to internalise social costs, shifting the private cost curve upward "
        "to match the social cost curve."
    )
    doc.add_paragraph(
        "Implementation: The penalty is applied per-Business Unit, not as a flat group-level deduction. "
        "This ensures that high-carbon BUs (e.g., Electronics with CI=60) bear proportionally heavier "
        "costs than low-carbon BUs (e.g., Software with CI=10), creating internal pressure for "
        "portfolio restructuring."
    )
    p = doc.add_paragraph()
    run = p.add_run("Formula:")
    run.bold = True
    add_formula(doc,
        "Penalty = BU_Carbon_Emissions × Tax_Rate_Per_Ton\n"
        "Where: BU_Carbon_Emissions = Carbon_Intensity × Revenue_Base / 1,000,000"
    )
    doc.add_paragraph('Worked Example:', style='List Bullet')
    doc.add_paragraph(
        'Electronics BU: CI = 60, Revenue = $22M, Tax Rate = $85/ton',
        style='List Bullet 2',
    )
    doc.add_paragraph(
        'Estimated Tonnes = 60 × 22,000,000 / 1,000,000 = 1,320 tonnes CO₂e',
        style='List Bullet 2',
    )
    doc.add_paragraph(
        'Penalty = 1,320 × $85 = $112,200 added to BU OPEX',
        style='List Bullet 2',
    )
    doc.add_paragraph(
        'Software BU: CI = 10, Revenue = $20M → 200 tonnes × $85 = $17,000 (6.6× less)',
        style='List Bullet 2',
    )

    doc.add_heading('16.2.2 Coasian Property Rights (Coase, 1960)', level=3)
    doc.add_paragraph(
        "Ronald Coase's theorem argues that when property rights over common-pool resources are "
        "well-defined, externalities can be resolved through private negotiation — but only when "
        "transaction costs are low. In the simulation, Coasian friction models the operational "
        "overhead of legal disputes over shared resources (principally water rights)."
    )
    add_theory_citation(
        doc,
        "Coase, R. H. (1960). 'The Problem of Social Cost.' Journal of Law and Economics, 3, 1–44. "
        "— Transaction costs rise when property rights are contested, creating operational friction "
        "that reduces efficiency."
    )
    p = doc.add_paragraph()
    run = p.add_run("Formula:")
    run.bold = True
    add_formula(doc,
        "Friction = Base_Friction × (1 + Water_Dependency × Water_Stress)\n"
        "If Legal_Dispute_Active: Friction × 2.0\n"
        "OPEX_Increase = BU_OPEX × Friction\n"
        "Friction capped at 20% of OPEX"
    )
    doc.add_paragraph(
        "Facilitator Note: The Coasian legal dispute flag is activated automatically when a "
        "Polycentric Water Shock fires in Round 8, and persists for all subsequent rounds. "
        "This models the real-world stickiness of legal proceedings — once litigation begins, "
        "it imposes ongoing costs even after the initial crisis subsides.",
    )

    doc.add_heading('16.2.3 Polycentric Governance (Ostrom, 2009)', level=3)
    doc.add_paragraph(
        "Elinor Ostrom's polycentric governance framework demonstrates that complex regulatory "
        "systems with multiple overlapping jurisdictions can be more effective than monolithic "
        "top-down mandates — but they also create asymmetric compliance burdens. In the simulation, "
        "when two or more regulatory instruments are simultaneously active, each BU receives an "
        "asymmetric burden proportional to its industrial and geographic footprint."
    )
    add_theory_citation(
        doc,
        "Ostrom, E. (2009). 'A Polycentric Approach for Coping with Climate Change.' "
        "World Bank Policy Research Working Paper No. 5095. — Multi-level governance creates "
        "differentiated regulatory pressure across heterogeneous actors."
    )
    p = doc.add_paragraph()
    run = p.add_run("Formula:")
    run.bold = True
    add_formula(doc,
        "Carbon_Weight = MIN(CI / 100, 1.0) × 0.05\n"
        "Water_Weight  = MIN(Water_Dependency, 1.0) × 0.03\n"
        "Total_Burden  = Revenue × (Carbon_Weight + Water_Weight)"
    )
    doc.add_paragraph('Asymmetric Burden Comparison:', style='List Bullet')

    # Burden comparison table
    table = doc.add_table(rows=5, cols=5)
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ['Business Unit', 'Carbon Intensity', 'Water Dependency', 'Burden Rate', 'Burden Cost']
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
        for run in table.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
    data = [
        ('Pharmaceuticals', '45', '0.60', '4.05%', '$729K'),
        ('Electronics', '60', '0.80', '5.40%', '$1.19M'),
        ('Consumer Goods', '30', '0.30', '2.40%', '$360K'),
        ('Software', '10', '0.10', '0.80%', '$160K'),
    ]
    for r, row_data in enumerate(data, 1):
        for c, val in enumerate(row_data):
            table.rows[r].cells[c].text = val

    doc.add_paragraph()  # spacer

    # ── 16.3 Middleware Intercept Architecture ────────────────
    doc.add_heading('16.3 Middleware Intercept Architecture', level=2)
    doc.add_paragraph(
        "The sandbox operates as a 3-phase middleware pipeline embedded within the "
        "run_new_engines() function in round_logic.py. This architecture ensures that "
        "sandbox effects are applied before values finalize, without disrupting the "
        "core engine's post_tick processing."
    )

    doc.add_heading('Phase 1: State Transition Intercept', level=3)
    doc.add_paragraph(
        "Before any standard sandbox instrument effects are applied, the intercept function "
        "evaluates per-BU Pigouvian penalties, checks Carbon Minsky Moment thresholds, "
        "calculates Coasian friction, applies polycentric burdens, and evaluates exogenous "
        "event trigger conditions for Rounds 7–9."
    )

    doc.add_heading('Phase 2: Standard Instrument Effects', level=3)
    doc.add_paragraph(
        "The existing regulatory instrument effects (carbon tax compliance costs, emissions "
        "trading scheme adjustments, mandatory disclosure overhead) are applied using the "
        "standard apply_sandbox_effects() function with time-series escalation and decay."
    )

    doc.add_heading('Phase 3: Agent Cross-Wiring', level=3)
    doc.add_paragraph(
        "After all sandbox effects have modified the game state, the cross-wiring function "
        "checks whether the cumulative impact has pushed any autonomous stakeholder agent "
        "past their trigger threshold. If so, the agent fires immediately, creating a "
        "cascading crisis event visible in the player's cockpit."
    )

    # Pipeline table
    doc.add_heading('Execution Order', level=3)
    pipe_table = doc.add_table(rows=4, cols=3)
    pipe_table.style = 'Light Grid Accent 1'
    pipe_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    pipe_headers = ['Phase', 'Function', 'Purpose']
    for i, h in enumerate(pipe_headers):
        pipe_table.rows[0].cells[i].text = h
        for run in pipe_table.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
    pipe_data = [
        ('1. Intercept', 'intercept_state_transition()', 'Pigouvian penalty, Minsky check, Coasian friction, polycentric burden, exogenous event evaluation'),
        ('2. Effects', 'apply_sandbox_effects()', 'Standard instrument compliance costs with time-series escalation and decay (Goodhart\'s Law)'),
        ('3. Cross-Wire', 'crosswire_sandbox_to_agents()', 'Eleanor Carson regulatory fine, Marcus Chen-Hoffmann divestment cascade, Megha Patrike community injunction'),
    ]
    for r, row_data in enumerate(pipe_data, 1):
        for c, val in enumerate(row_data):
            pipe_table.rows[r].cells[c].text = val
    doc.add_paragraph()

    # ── 16.4 Carbon Minsky Moment ────────────────────────────
    doc.add_heading('16.4 The Carbon Minsky Moment', level=2)
    doc.add_paragraph(
        "Named after Hyman Minsky's financial instability hypothesis and Mark Carney's 2015 "
        "'Tragedy of the Horizon' speech at Lloyd's of London, the Carbon Minsky Moment simulates "
        "the tipping point where accumulated Natural Capital Debt becomes unmanageable due to "
        "compounding interest spirals."
    )
    add_theory_citation(
        doc,
        "Carney, M. (2015). 'Breaking the Tragedy of the Horizon — Climate Change and Financial "
        "Stability.' Speech at Lloyd's of London, 29 September 2015. — Financial assets become "
        "stranded when climate externalities are suddenly priced in, creating Minsky-type instability."
    )

    p = doc.add_paragraph()
    run = p.add_run("Trigger Conditions:")
    run.bold = True
    doc.add_paragraph(
        'Any BU with Natural Capital Debt > 200 AND an active sandbox carbon tax',
        style='List Bullet',
    )
    doc.add_paragraph('Available in Rounds 7, 8, and 9', style='List Bullet')
    doc.add_paragraph('Can be force-triggered via God Mode at any round', style='List Bullet')

    p = doc.add_paragraph()
    run = p.add_run("Effects:")
    run.bold = True
    doc.add_paragraph('NCD interest rate increased by +200 basis points (compounding)', style='List Bullet')
    doc.add_paragraph('Corporate treasury hit: −5%', style='List Bullet')
    doc.add_paragraph('Group reputation: −8 points', style='List Bullet')
    doc.add_paragraph('Forced divestment mode activated', style='List Bullet')

    p = doc.add_paragraph()
    run = p.add_run("Mathematical Example:")
    run.bold = True
    add_formula(doc,
        "Given: Electronics NCD = 300, Interest Rate before = 0.05 + (300 × 0.0001) = 0.08\n"
        "Minsky +200bps: Rate Increase = 200 / 10,000 = 0.02\n"
        "Extra Interest = 300 × 0.02 = $6.00 added to NCD per round\n"
        "New NCD = 300 × (1 + 0.02) = $306.00 (BEFORE normal interest compounding)\n"
        "Combined with normal interest: NCD_Next = 306 × 1.08 = $330.48\n"
        "Without Minsky: NCD_Next = 300 × 1.08 = $324.00 (Minsky adds $6.48/round)"
    )
    doc.add_paragraph(
        "Facilitator Debrief Point: The compounding effect may seem small in a single round, but "
        "over Rounds 7–10 it creates an exponential debt spiral. Ask students: 'At what point should "
        "you have invested in decarbonisation to avoid this outcome? What does this tell us about the "
        "cost of deferred climate action?'"
    )

    # ── 16.5 Exogenous Crisis Scenarios ──────────────────────
    doc.add_heading('16.5 Operational Crisis Scenarios (Rounds 7–9)', level=2)
    doc.add_paragraph(
        "Three configurable crisis scenarios can be triggered automatically (when conditions are met) "
        "or manually via the facilitator's God Mode panel. Each scenario is designed to test a "
        "different dimension of systemic resilience."
    )

    # Crisis table
    crisis_table = doc.add_table(rows=4, cols=5)
    crisis_table.style = 'Light Grid Accent 1'
    crisis_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_headers = ['Scenario', 'Trigger', 'Rounds', 'Primary Effect', 'Theoretical Base']
    for i, h in enumerate(c_headers):
        crisis_table.rows[0].cells[i].text = h
        for run in crisis_table.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
    c_data = [
        ('💥 Carbon Minsky Moment', 'NCD > 200 + carbon tax active', '7, 8, 9',
         '+200bps NCD interest, −5% treasury, −8 reputation',
         'Carney (2015), Minsky (1986)'),
        ('⚖️ CSDDD Enforcement', 'Reputation < 40 + whistleblower (60% probability)', '7, 8, 9',
         '€30M fine, +15 governance risk (worst BU), −12 reputation',
         'EU CS3D (2024)'),
        ('🌊 Polycentric Water Shock', 'Water Stress Index ≥ 0.6', '8 only',
         '+15% OPEX all BUs, −15 SLO, $5M legal costs, Coasian dispute activated',
         'Coase (1960), Ostrom (2009)'),
    ]
    for r, row_data in enumerate(c_data, 1):
        for c, val in enumerate(row_data):
            crisis_table.rows[r].cells[c].text = val
    doc.add_paragraph()

    doc.add_heading('16.5.1 CSDDD Enforcement Action', level=3)
    doc.add_paragraph(
        "The Corporate Sustainability Due Diligence Directive (CS3D), adopted by the European Union "
        "in 2024, mandates that large companies conduct environmental and human rights due diligence "
        "across their value chains. Non-compliance triggers civil liability and administrative sanctions."
    )
    doc.add_paragraph(
        "In the simulation, when group reputation drops below 40 (indicating persistent governance "
        "failures), a whistleblower event has a 60% probability of triggering an enforcement action. "
        "The worst-performing BU (by social license score) receives a governance risk spike of +15 points, "
        "while the group absorbs a €30M fine from the corporate treasury."
    )
    add_theory_citation(
        doc,
        "European Parliament (2024). Corporate Sustainability Due Diligence Directive (CS3D). "
        "Directive (EU) 2024/1760. — Establishes mandatory due diligence with civil liability."
    )

    doc.add_heading('16.5.2 Polycentric Water Shock', level=3)
    doc.add_paragraph(
        "When the simulation's Water Stress Index reaches critical levels (≥ 0.6), community activist "
        "Megha Patrike (NPC stakeholder) obtains a court injunction blocking facility access. This models "
        "the real-world intersection of Coasian property rights and Ostrom's polycentric governance: "
        "a local actor enforces resource boundaries that national regulatory frameworks have failed to protect."
    )
    doc.add_paragraph(
        "The shock applies a blanket +15% OPEX increase to all BUs (modelling supply chain disruption), "
        "deducts $5M in legal costs from the treasury, and permanently activates the Coasian legal "
        "dispute flag — meaning friction costs persist for all subsequent rounds."
    )

    # ── 16.6 Agent Cross-Wiring ──────────────────────────────
    doc.add_heading('16.6 Autonomous Agent Cross-Wiring', level=2)
    doc.add_paragraph(
        "The sandbox controller's Phase 3 checks whether cumulative sandbox effects have pushed "
        "autonomous stakeholder agents past their trigger thresholds. This creates pedagogically "
        "powerful moments where a 'regulatory shock' cascades into a 'stakeholder crisis' — "
        "demonstrating systems thinking in real time."
    )

    agent_table = doc.add_table(rows=3, cols=4)
    agent_table.style = 'Light Grid Accent 1'
    agent_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    a_headers = ['Agent', 'Trigger Condition', 'Action', 'Financial Impact']
    for i, h in enumerate(a_headers):
        agent_table.rows[0].cells[i].text = h
        for run in agent_table.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
    a_data = [
        ('🏛️ Commissioner Eleanor Carson\n(The Regulator)',
         'Average Governance Risk > 55',
         'Emergency 4% revenue fine; tolerance −20',
         'Fine = Total_Revenue × 0.04'),
        ('📉 Marcus Chen-Hoffmann\n(The Institutional Investor)',
         'Group EBITDA < 0\n(negative operating profit)',
         'Divestment fire sale; tolerance −25',
         'Treasury Hit = Treasury × 0.08'),
    ]
    for r, row_data in enumerate(a_data, 1):
        for c, val in enumerate(row_data):
            agent_table.rows[r].cells[c].text = val
    doc.add_paragraph()

    doc.add_paragraph(
        "Facilitator Debrief Point: When Eleanor Carson's fine triggers after a CSDDD enforcement "
        "action, ask students: 'Did the regulation cause the fine, or did your pre-existing governance "
        "failures make you vulnerable to it? How could earlier investment in governance have prevented "
        "this cascading outcome?' This is a powerful illustration of Meadows' leverage point #3: "
        "the rules of the system (subsidies, punishments, constraints)."
    )

    # ── 16.7 God Mode Controls ───────────────────────────────
    doc.add_heading('16.7 Facilitator God Mode Controls', level=2)
    doc.add_paragraph(
        "All sandbox functionality is gated behind the regulatory_sandbox_enabled toggle in the "
        "God Mode panel. Agent cross-wiring additionally requires npc_stakeholders_enabled = true. "
        "Facilitators can manually trigger any exogenous event regardless of whether natural "
        "trigger conditions are met."
    )

    doc.add_heading('Available API Endpoints', level=3)
    endpoint_table = doc.add_table(rows=5, cols=3)
    endpoint_table.style = 'Light Grid Accent 1'
    endpoint_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    e_headers = ['Method', 'Endpoint', 'Purpose']
    for i, h in enumerate(e_headers):
        endpoint_table.rows[0].cells[i].text = h
        for run in endpoint_table.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
    e_data = [
        ('POST', '/api/{id}/regulatory-sandbox/activate', 'Activate a regulatory instrument (carbon_tax, emissions_trading, etc.)'),
        ('GET', '/api/{id}/regulatory-sandbox/instruments', 'List all available regulatory instruments'),
        ('GET', '/api/{id}/regulatory-sandbox/exogenous-events', 'List exogenous events with trigger status'),
        ('POST', '/api/{id}/regulatory-sandbox/trigger-event', 'Force-trigger a specific exogenous event'),
    ]
    for r, row_data in enumerate(e_data, 1):
        for c, val in enumerate(row_data):
            endpoint_table.rows[r].cells[c].text = val
    doc.add_paragraph()

    doc.add_heading('Suggested Facilitator Workflow', level=3)
    doc.add_paragraph(
        '1. Pre-Session: Enable "Regulatory Sandbox" and "NPC Stakeholders" toggles via God Mode.',
        style='List Number',
    )
    doc.add_paragraph(
        '2. Round 5–6: Activate a carbon tax ($85/ton recommended) via the sandbox panel. '
        'Observe student reactions to the per-BU cost differential.',
        style='List Number',
    )
    doc.add_paragraph(
        '3. Round 7: If any BU has NCD > 200, the Carbon Minsky Moment will auto-trigger. '
        'If not, consider force-triggering via God Mode for pedagogical impact.',
        style='List Number',
    )
    doc.add_paragraph(
        '4. Round 8: If Water Stress Index ≥ 0.6, the Polycentric Water Shock auto-fires. '
        'This is the strongest cascade scenario — OPEX +15% + Coasian friction activated.',
        style='List Number',
    )
    doc.add_paragraph(
        '5. Post-Game Debrief: Use the intercept_log (visible in session diagnostics) to '
        'walk students through the exact sequence of cause and effect.',
        style='List Number',
    )

    # ── 16.8 Debrief Questions ───────────────────────────────
    doc.add_heading('16.8 Suggested Debrief Questions', level=2)

    debrief_qs = [
        (
            "Pigouvian Efficiency:",
            "Was the carbon tax effective at changing BU-level behaviour? Did students restructure "
            "their portfolio, or did they simply absorb the cost? What does Pigou's theory predict "
            "about the 'correct' tax rate?"
        ),
        (
            "Coasian Negotiation:",
            "When the Water Shock activated Coasian friction, did students attempt to negotiate "
            "with affected stakeholders, or did they treat the court injunction as a fixed cost? "
            "What does Coase's theorem suggest about the role of transaction costs in this outcome?"
        ),
        (
            "Polycentric Complexity:",
            "When multiple regulations were simultaneously active, did the asymmetric burden "
            "create winners and losers within the portfolio? How does Ostrom's framework explain "
            "why localized governance may be more effective than a single global carbon price?"
        ),
        (
            "Minsky Spiral:",
            "At what point did the NCD interest spiral become unmanageable? Could earlier "
            "decarbonisation investment have avoided the Minsky Moment entirely? What parallels "
            "exist in real-world climate finance (e.g., stranded fossil fuel assets)?"
        ),
        (
            "Agent Cascades:",
            "When Eleanor Carson imposed the 4% revenue fine, was this 'unfair' regulation or "
            "a predictable consequence of accumulated governance risk? How does Meadows' leverage "
            "point framework (#3: rules of the system) explain this cascade?"
        ),
        (
            "Systems Thinking:",
            "Map the full cascade from 'carbon tax activated' to 'divestment fire sale'. "
            "How many feedback loops can you identify? Which were reinforcing and which were "
            "balancing? Where were the intervention points you missed?"
        ),
    ]

    for bold_prefix, question in debrief_qs:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(bold_prefix + " ")
        run.bold = True
        run.font.size = Pt(11)
        run = p.add_run(question)
        run.font.size = Pt(11)

    # ── Save ─────────────────────────────────────────────────
    output_path = os.path.join(base_dir, "Muressons_Simulation_Briefings ver 10.docx")
    doc.save(output_path)
    print(f"Successfully created {output_path}")


if __name__ == '__main__':
    append_regulatory_sandbox_section()
