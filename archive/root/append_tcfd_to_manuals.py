"""
Append TCFD Climate Scenario Analysis sections to both the
Student Manual (v4 → v5) and Facilitator Manual (v3 → v4).

Follows the established append pattern used by append_brsr_track_manuals.py.
"""
import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn


# ═══════════════════════════════════════════════════════════════
#  SHARED UTILITIES
# ═══════════════════════════════════════════════════════════════

def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(16, 185, 129)  # Muressons emerald


def add_styled_paragraph(doc, text, bold_prefix=None, italic=False):
    """Add a paragraph with optional bold prefix."""
    p = doc.add_paragraph()
    if bold_prefix:
        run = p.add_run(bold_prefix)
        run.bold = True
    run = p.add_run(text)
    run.italic = italic
    return p


def add_table_row(table, cells_text, bold_first=True):
    """Add a row to an existing table."""
    row = table.add_row()
    for i, txt in enumerate(cells_text):
        cell = row.cells[i]
        p = cell.paragraphs[0]
        run = p.add_run(str(txt))
        run.font.size = Pt(9)
        if bold_first and i == 0:
            run.bold = True


def create_scenario_table(doc):
    """Create the 3-scenario comparison table used in both manuals."""
    table = doc.add_table(rows=1, cols=6)
    table.style = 'Light Grid Accent 1'

    headers = ['Scenario', 'Temp. Path', 'NGFS Category',
               'Carbon Price Trajectory', 'Key Risk', 'Strategic Implication']
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        p = cell.paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.size = Pt(9)

    add_table_row(table, [
        'Net Zero 2050',
        '1.5°C',
        'Orderly',
        '$50 → $250/tCO₂',
        'HIGH transition risk, LOW physical risk',
        'Front-load decarbonisation CapEx; green tech premium turns negative',
    ])
    add_table_row(table, [
        'Delayed Transition',
        '2°C',
        'Disorderly',
        '$30 → $350/tCO₂ (shock)',
        'BOTH transition AND physical risks elevated',
        'Build financial buffers; prepare for carbon price shock',
    ])
    add_table_row(table, [
        'Current Policies',
        '4°C',
        'Hot house world',
        '$20 → $40/tCO₂',
        'CATASTROPHIC physical risk, low transition risk',
        'Supply chain resilience; healthcare demand surge opportunity',
    ])
    return table


# ═══════════════════════════════════════════════════════════════
#  STUDENT MANUAL — TCFD APPENDIX
# ═══════════════════════════════════════════════════════════════

def append_tcfd_to_student_manual(file_path):
    doc = Document(file_path)

    doc.add_page_break()
    add_heading(doc, "Appendix: TCFD Climate Scenario Analysis", level=1)

    # ── Introduction ──
    p = doc.add_paragraph()
    p.add_run("The Task Force on Climate-related Financial Disclosures (TCFD) ").bold = True
    p.add_run(
        "provides the globally recognised framework for assessing how climate change "
        "affects your portfolio. In the Muressons simulation, the TCFD Scenario Analysis "
        "tool projects your company's financial exposure across three distinct climate "
        "pathways aligned with the Network for Greening the Financial System (NGFS)."
    )

    add_heading(doc, "Why TCFD Matters for Your Strategy", level=2)
    doc.add_paragraph(
        "Real-world boards and investors increasingly demand TCFD-aligned scenario "
        "analysis. Companies that cannot articulate their climate risk exposure face "
        "higher cost of capital, investor exit, and regulatory penalties. In Muressons, "
        "you can access the Climate Scenario Dashboard from the cockpit's Climate tab "
        "to stress-test your portfolio against these futures."
    )

    add_heading(doc, "The Three NGFS-Aligned Scenarios", level=2)
    doc.add_paragraph(
        "Your analysis runs across three scenarios, each representing a fundamentally "
        "different climate–policy–technology trajectory:"
    )

    create_scenario_table(doc)

    add_heading(doc, "What the Dashboard Shows You", level=2)
    doc.add_paragraph(
        "The Climate Scenario Dashboard (accessible via the 🌡️ Climate tab in the "
        "right panel) provides:"
    )

    metrics = [
        ("Revenue Impact by BU: ",
         "Each business unit is projected forward under the scenario's demand shift. "
         "Software may thrive in the 1.5°C world while Consumer Goods contracts; "
         "in the 4°C hothouse, Healthcare demand surges but Electronics supply chains collapse."),
        ("Annual Carbon Cost: ",
         "Calculated from your average carbon intensity × estimated emissions × the "
         "scenario's carbon price at the analysis horizon. A team with high carbon intensity "
         "faces existential costs under the Disorderly 2°C pathway ($350/tCO₂)."),
        ("Physical Risk Assessment: ",
         "Multiplied from a 2% baseline loss rate. The Hothouse 4°C scenario applies "
         "a 4× multiplier, representing extreme weather, crop failure, and supply chain "
         "disruption. Your resilience factor (built through strategic investments) mitigates this."),
        ("Stranded Asset Exposure: ",
         "Estimates what percentage of your property, plant & equipment becomes worthless "
         "under each scenario. Under Orderly 1.5°C, 35% of fossil-linked assets are stranded; "
         "under Hothouse 4°C, only 10% (because no transition occurs)."),
        ("Transition Opportunity Score: ",
         "Composite of your Reputation, Social License, Workforce Readiness, and carbon "
         "intensity. A score above 70 means 'well positioned'; below 45 signals 'high vulnerability'."),
        ("Nature Risk (TNFD): ",
         "If biodiversity data is active, the dashboard overlays a Taskforce on Nature-related "
         "Financial Disclosures (TNFD) risk assessment showing Ecosystem Health, Biodiversity "
         "Dependency, and the recommended LEAP approach."),
    ]

    for bold, text in metrics:
        p = doc.add_paragraph()
        p.add_run(bold).bold = True
        p.add_run(text)

    add_heading(doc, "Compare Mode", level=3)
    doc.add_paragraph(
        "Toggle 'Compare' to see all three scenarios side by side with animated bars "
        "showing revenue impact, carbon cost, physical loss, and overall risk gauges. "
        "This view directly mirrors how TCFD-aligned reports present their multi-scenario "
        "comparison matrices."
    )

    add_heading(doc, "Strategic Implications", level=2)
    doc.add_paragraph(
        "The key TCFD principle is 'strategic resilience under uncertainty'. A robust "
        "corporate strategy should perform acceptably across ALL scenarios, not just "
        "optimise for one. As you make pillar decisions each round, consider:"
    )

    implications = [
        "Under 1.5°C: Is your decarbonisation pace fast enough to avoid punitive carbon costs?",
        "Under 2°C: Do you have sufficient financial buffers to absorb the carbon price shock from $40 to $150/tCO₂?",
        "Under 4°C: Can your supply chains survive catastrophic physical disruption? Is your healthcare exposure an opportunity?",
        "Across all: Does your overall M_R (Regenerative Multiple) position you as a leader or a laggard?",
    ]
    for imp in implications:
        doc.add_paragraph(imp, style='List Bullet')

    add_heading(doc, "Theoretical Foundation", level=2)
    doc.add_paragraph(
        "TCFD (2017): Recommendations of the Task Force on Climate-related Financial "
        "Disclosures — the global standard for climate risk disclosure.",
        style='List Bullet'
    )
    doc.add_paragraph(
        "NGFS (2022): Network for Greening the Financial System — provides the central "
        "bank-aligned scenario framework (Orderly, Disorderly, Hot House).",
        style='List Bullet'
    )
    doc.add_paragraph(
        "IEA (2023): International Energy Agency World Energy Outlook — scenario "
        "projections for energy demand, carbon prices, and technology adoption.",
        style='List Bullet'
    )
    doc.add_paragraph(
        "Carbon Tracker Initiative: Pioneered the 'stranded assets' methodology used "
        "to estimate fossil-fuel write-down exposure.",
        style='List Bullet'
    )

    out_path = "Muressons_Student_Manual_v5.docx"
    doc.save(out_path)
    print(f"Created {out_path}")


# ═══════════════════════════════════════════════════════════════
#  FACILITATOR MANUAL — TCFD SUPPLEMENT
# ═══════════════════════════════════════════════════════════════

def append_tcfd_to_facilitator_manual(file_path):
    doc = Document(file_path)

    doc.add_page_break()
    add_heading(doc, "Module Supplement: TCFD Climate Scenario Analysis", level=1)

    doc.add_paragraph(
        "The TCFD Scenario Analysis engine (SI-4) is a pure-function analytical tool "
        "that allows players to stress-test their portfolio against three NGFS-aligned "
        "climate pathways. It produces no state mutation — it is purely diagnostic. "
        "This section covers the pedagogical goals, facilitator controls, classroom "
        "integration, and debriefing strategies."
    )

    # ── Pedagogical Goals ──
    add_heading(doc, "Pedagogical Goals", level=2)
    doc.add_paragraph(
        "The TCFD module develops the following competencies:"
    )
    goals = [
        "Scenario Thinking: Students learn to assess strategy under deep uncertainty, moving beyond single-point forecasts.",
        "Climate Risk Literacy: Distinguishing between transition risk (policy, technology, market) and physical risk (extreme weather, sea-level rise).",
        "Stranded Asset Awareness: Understanding why fossil-linked assets lose value under ambitious climate policy.",
        "TCFD / TNFD Disclosure: Practical exposure to the disclosure frameworks increasingly mandated by regulators.",
        "Strategic Resilience: Identifying strategies that are robust across multiple scenarios rather than optimal for just one.",
    ]
    for g in goals:
        doc.add_paragraph(g, style='List Bullet')

    # ── The Three Scenarios ──
    add_heading(doc, "The Three Climate Scenarios", level=2)
    doc.add_paragraph(
        "The engine models three NGFS-aligned pathways. Each scenario has distinct "
        "carbon price trajectories, physical risk multipliers, demand shifts by sector, "
        "and stranded asset exposures:"
    )

    create_scenario_table(doc)

    # ── Dashboard Access & Controls ──
    add_heading(doc, "Dashboard Access & Controls", level=2)

    add_styled_paragraph(doc, (
        "The TCFD dashboard is accessible via the 🌡️ Climate tab in the right "
        "panel of the player cockpit. It fetches data from the backend API endpoint "
        "GET /api/simulations/{session_id}/tcfd-scenarios."
    ), bold_prefix="Player Access: ")

    add_styled_paragraph(doc, (
        "TCFD can be toggled on/off per cohort via the God Mode toggle "
        "'tcfd_scenarios_enabled' (default: ON). It can also be set during cohort "
        "creation in the CreateCohortModal."
    ), bold_prefix="God Mode Toggle: ")

    add_styled_paragraph(doc, (
        "The analysis uses the player's current portfolio state — carbon intensity, "
        "revenue base, social license, reputation, and workforce readiness — to "
        "generate forward projections. As players decarbonise and invest strategically, "
        "their scenario outputs improve dynamically."
    ), bold_prefix="Dynamic Data: ")

    # ── Metrics Deep-Dive ──
    add_heading(doc, "Metrics Calculated per Scenario", level=2)

    metrics_table = doc.add_table(rows=1, cols=3)
    metrics_table.style = 'Light Grid Accent 1'
    for i, h in enumerate(['Metric', 'Calculation', 'Teaching Use']):
        run = metrics_table.rows[0].cells[i].paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(9)

    metrics = [
        ['Revenue Impact (%)',
         'BU revenue × demand_shift^(horizon/5)',
         'Illustrates sector-specific vulnerability to climate transitions'],
        ['Annual Carbon Cost',
         'avg_CI × BU_count × 1000 × carbon_price',
         'Shows the financial materiality of carbon intensity'],
        ['Physical Risk',
         'Treasury × 2% × phys_multiplier × (1 - resilience)',
         'Quantifies the protective value of resilience investments'],
        ['Stranded Assets',
         'Total PPE × stranded_pct × 80% write-down',
         'Teaches the concept of fossil-asset obsolescence'],
        ['Opportunity Score',
         '(Rep×0.3 + SLO×0.3 + WFR×0.2 + (100-CI)×0.2) × 100',
         'Multi-dimensional readiness assessment'],
        ['Nature Risk (TNFD)',
         '(100 - EHI)/100 × bio_dependency × phys_mult × 100',
         'Connects biodiversity loss to financial risk'],
    ]
    for m in metrics:
        add_table_row(metrics_table, m, bold_first=True)

    # ── Classroom Integration ──
    add_heading(doc, "Classroom Integration Strategies", level=2)

    add_heading(doc, "Round 2 (Post-Materiality)", level=3)
    doc.add_paragraph(
        "After students complete the materiality matrix, introduce the TCFD Climate tab. "
        "Prompt: 'You've identified your material ESG issues. Now, how would a 1.5°C "
        "vs. 4°C world change which issues are most material?' This bridges the "
        "Double Materiality concept with forward-looking scenario analysis."
    )

    add_heading(doc, "Round 5 (Mid-Game Checkpoint)", level=3)
    doc.add_paragraph(
        "During the mid-game checkpoint, have teams compare their TCFD dashboard data. "
        "Use the Compare mode to project all three scenarios side by side. Discussion "
        "prompt: 'Which team has the most resilient portfolio — one that performs "
        "acceptably across ALL three scenarios?' This teaches the TCFD principle "
        "of strategic resilience under uncertainty."
    )

    add_heading(doc, "Round 8–9 (Pre-Endgame)", level=3)
    doc.add_paragraph(
        "As teams approach the grand finale, prompt them to revisit their TCFD scenarios "
        "to evaluate whether their mid-game strategic pivots have improved or degraded "
        "their climate resilience. Prompt: 'Has your carbon intensity decreased enough "
        "to survive the Disorderly 2°C carbon price shock?' Link to Stranded Asset theory "
        "(Carbon Tracker Initiative)."
    )

    add_heading(doc, "Post-Game Debrief", level=3)
    doc.add_paragraph(
        "Include TCFD scenario data in the debrief report. Compare teams' final "
        "Overall Risk Rating across scenarios. Teams with high Opportunity Scores "
        "(>70) demonstrate genuine understanding of climate-resilient strategy. "
        "Use the nature risk overlay to discuss TNFD and the emerging 'double materiality' "
        "of nature and climate disclosure frameworks."
    )

    # ── Facilitator Talking Points ──
    add_heading(doc, "Facilitator Talking Points", level=2)

    talking_points = [
        ("On Carbon Pricing: ",
         "'In the real world, the EU Emissions Trading System already prices carbon "
         "at €90-100/tCO₂. The Orderly 1.5°C scenario projects $250/tCO₂ by 2050. "
         "What does this mean for your most carbon-intensive business unit?'"),
        ("On Stranded Assets: ",
         "'Carbon Tracker estimates that $900 billion of fossil-fuel assets are at "
         "risk of stranding. In your simulation, how much of your PPE is exposed? "
         "What does the 35% stranded figure under 1.5°C mean for your balance sheet?'"),
        ("On Physical Risk: ",
         "'The 4°C Hothouse scenario applies a 4× physical risk multiplier. "
         "Munich Re reported $120bn in natural catastrophe losses in 2022. "
         "How much does your treasury lose annually under this scenario?'"),
        ("On TCFD Compliance: ",
         "'TCFD is now mandatory in the UK, EU (via CSRD), Japan, Singapore, and "
         "New Zealand. How does your scenario analysis demonstrate compliance? "
         "What would investors say about your Opportunity Score?'"),
        ("On the TNFD Extension: ",
         "'The Taskforce on Nature-related Financial Disclosures builds on TCFD "
         "by adding biodiversity dependency. Does your Ecosystem Health Index "
         "create additional exposure beyond climate?'"),
    ]
    for bold, text in talking_points:
        p = doc.add_paragraph()
        p.add_run(bold).bold = True
        p.add_run(text)

    # ── API Reference ──
    add_heading(doc, "Technical Reference", level=2)
    add_styled_paragraph(doc, (
        "GET /api/simulations/{session_id}/tcfd-scenarios — "
        "Returns all 3 scenarios with comparison matrix. "
        "Optional query param: ?scenario_id=orderly_1_5 for single scenario."
    ), bold_prefix="API Endpoint: ")
    add_styled_paragraph(doc, (
        "tcfd_scenarios.py → run_scenario_analysis() and get_scenario_comparison(). "
        "Pure-function module with no state mutation."
    ), bold_prefix="Backend Module: ")
    add_styled_paragraph(doc, (
        "TCFDScenarioDashboard.js — self-contained React component rendered in the "
        "right panel Climate tab. Features single-scenario and compare modes with "
        "animated arc gauges, BU revenue projection bars, and strategic implications."
    ), bold_prefix="Frontend Component: ")

    out_path = "Muressons_Facilitator_Manual_v4.docx"
    doc.save(out_path)
    print(f"Created {out_path}")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    student_src = "Muressons_Student_Manual_v4.docx"
    facilitator_src = "Muressons_Facilitator_Manual_v3.docx"

    if os.path.exists(student_src):
        append_tcfd_to_student_manual(student_src)
    else:
        print(f"File {student_src} not found — skipping student manual.")

    if os.path.exists(facilitator_src):
        append_tcfd_to_facilitator_manual(facilitator_src)
    else:
        print(f"File {facilitator_src} not found — skipping facilitator manual.")
