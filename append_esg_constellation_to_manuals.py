"""
append_esg_constellation_to_manuals.py
---------------------------------------
Appends a detailed ESG Impact Constellation section to:
  - Muressons_Student_Manual_v5_with_CAROIC_with_CEO_Debrief.docx  (Player Manual)
  - Muressons_Facilitator_Manual_v4.docx                            (Facilitator Manual)

Outputs versioned copies:
  - ..._with_Constellation.docx
"""

import os
import docx
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE_DIR = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim"

STUDENT_MANUAL = os.path.join(BASE_DIR, "Muressons_Student_Manual_v5_with_CAROIC_with_CEO_Debrief.docx")
FACILITATOR_MANUAL = os.path.join(BASE_DIR, "Muressons_Facilitator_Manual_v4.docx")

# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────
def add_heading(doc, text, level=1):
    doc.add_heading(text, level=level)

def add_body(doc, text):
    p = doc.add_paragraph(text)
    p.style.font.size = Pt(11)
    return p

def add_bullet(doc, text):
    doc.add_paragraph(text, style='List Bullet')

def add_table_row(table, col1, col2, col3=None):
    row = table.add_row()
    row.cells[0].text = col1
    row.cells[1].text = col2
    if col3 is not None and len(row.cells) > 2:
        row.cells[2].text = col3

def add_code(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    p.paragraph_format.left_indent = Cm(1)
    return p


# ─────────────────────────────────────────────────────────────────
#  PLAYER SECTION  (Student Manual)
# ─────────────────────────────────────────────────────────────────
def add_player_section(doc):
    doc.add_page_break()

    add_heading(doc, 'Appendix: The ESG Impact Constellation', level=1)

    add_body(doc,
        "The ESG Impact Constellation is a live 3D visualizer embedded in your Executive Cockpit. "
        "It maps every strategic decision you make across all ten simulation rounds into an interactive "
        "star-chart, showing how your choices ripple forward — and sometimes loop back — across "
        "different ESG dimensions."
    )

    add_body(doc,
        "Think of it as your decision DNA made visible. After completing the simulation, the "
        "Constellation lets you examine which rounds had the biggest financial shocks, where you "
        "gained or lost reputation, and which early decisions set the conditions for your final outcome."
    )

    # ── What Each Node Represents ──
    add_heading(doc, 'What Each Node Represents', level=2)
    add_body(doc,
        "Every glowing sphere in the Constellation represents one completed round. "
        "The sphere's colour, size, and glow intensity all carry meaning:"
    )

    # Node table
    tbl = doc.add_table(rows=1, cols=3)
    tbl.style = 'Table Grid'
    hdr = tbl.rows[0].cells
    hdr[0].text = 'Round'
    hdr[1].text = 'Topic'
    hdr[2].text = 'ESG Dimension (Colour)'

    round_data = [
        ('R1', 'ESG Materiality',       'Environmental 🟢'),
        ('R2', 'Double Materiality',    'Governance 🟣'),
        ('R3', 'Scope 3 Supply Chain',  'Environmental 🟢'),
        ('R4', 'ESG Contagion',         'Social 🔵'),
        ('R5', 'Climate Risk',          'Environmental 🟢'),
        ('R6', 'AI Ethics',             'Governance 🟣'),
        ('R7', 'Circular Economy',      'Environmental 🟢'),
        ('R8', 'Water Stress',          'Environmental 🟢'),
        ('R9', 'Just Transition',       'Social 🔵'),
        ('R10','Activist Ultimatum',    'Mixed 🩵'),
    ]
    for r, topic, dim in round_data:
        add_table_row(tbl, r, topic, dim)

    doc.add_paragraph()  # spacer

    # ── Node Size ──
    add_heading(doc, 'Node Size = Financial Impact', level=2)
    add_body(doc,
        "The larger the sphere, the bigger the treasury shock your decision caused in that round. "
        "The size is calculated as:"
    )
    add_code(doc, "Node Size  =  |Treasury Change|  ÷  $5,000,000   (clamped between 0.15× and 0.5×)")
    add_body(doc,
        "A round where you committed to a costly green infrastructure investment, for example, "
        "will produce a noticeably larger sphere than a round where you only made a policy statement."
    )

    # ── Link Types ──
    add_heading(doc, 'Understanding the Connection Lines', level=2)
    add_body(doc,
        "Two types of curved lines connect the nodes:"
    )

    add_bullet(doc,
        "Solid teal curves — Sequential links. Every round automatically connects to the next. "
        "The thickness of the line reflects how dramatically your reputation changed between rounds. "
        "A reputation swing of ±20 points produces a thick, vivid line; a stable reputation produces "
        "a thin, quiet connection."
    )
    add_bullet(doc,
        "Dashed amber lines — Cross-causal links. These are the system's hardcoded memory. "
        "They appear between non-adjacent rounds that share a proven causal relationship:"
    )

    causal_table = doc.add_table(rows=1, cols=2)
    causal_table.style = 'Table Grid'
    causal_table.rows[0].cells[0].text = 'Causal Link'
    causal_table.rows[0].cells[1].text = 'What It Means'
    causal_data = [
        ('R3 → R5  (strength 0.6)',
         'Your Scope 3 Supply Chain decisions in R3 created the conditions for your Climate Risk '
         'exposure in R5. Cutting supplier emissions early reduces your R5 penalty.'),
        ('R4 → R7  (strength 0.4)',
         'ESG Contagion choices in R4 feed into Circular Economy incentives in R7. Social license '
         'earned in R4 unlocks higher-return circular options.'),
        ('R1 → R10 (strength 0.8)',
         'Your very first ESG Materiality framing echoes all the way to the Activist Ultimatum in '
         'R10. Groups that under-weighted material risks in R1 are far more vulnerable at the finale.'),
    ]
    for link, meaning in causal_data:
        row = causal_table.add_row()
        row.cells[0].text = link
        row.cells[1].text = meaning

    doc.add_paragraph()  # spacer

    # ── Background Nebula ──
    add_heading(doc, 'The Background Nebula = Your Reputation Health', level=2)
    add_body(doc,
        "The faint cloud that fills the entire scene is not decorative — it reflects your current "
        "reputation score at the end of the visible timeline:"
    )
    add_bullet(doc, "Green nebula  →  Reputation ≥ 65  (Thriving — stakeholders trust you)")
    add_bullet(doc, "Amber nebula  →  Reputation 40–64  (Cautious — goodwill is fragile)")
    add_bullet(doc, "Red nebula    →  Reputation < 40   (Critical — licence to operate at risk)")

    # ── Tooltip ──
    add_heading(doc, 'The Hover Tooltip', level=2)
    add_body(doc,
        "Click or hover on any node to reveal its round-level data card:"
    )
    add_bullet(doc, "Treasury Δ — Cash gained or lost during that round (shown in $K or $M)")
    add_bullet(doc, "Reputation Δ — Points gained or lost with stakeholders")
    add_bullet(doc, "Carbon Δ — Change in tCO₂e emissions (green = reduction, red = increase)")

    # ── Timeline Slider ──
    add_heading(doc, 'The Timeline Slider', level=2)
    add_body(doc,
        "The slider at the bottom of the screen lets you replay your journey round by round. "
        "Drag it left to remove later rounds from the view, watching the constellation contract "
        "to its earlier state. This is especially useful in debrief to trace how a single early "
        "decision cascade into later outcomes."
    )

    # ── Filter Bar ──
    add_heading(doc, 'ESG Filter Bar', level=2)
    add_body(doc,
        "Use the filter buttons (All / 🌱 E / 👥 S / 🏛️ G) to isolate one ESG dimension at a time. "
        "Nodes belonging to the selected dimension will glow at full intensity; all others fade. "
        "This reveals whether your strategy was balanced across E, S, and G or concentrated in one pillar."
    )

    # ── What to Look For ──
    add_heading(doc, 'What to Look For in the Debrief', level=2)
    add_body(doc,
        "When reviewing your Constellation after the simulation, ask yourself:"
    )
    add_bullet(doc, "Are the nodes roughly similar in size, or are one or two rounds dramatically larger? "
                    "Outliers reveal the moments of highest financial risk-taking.")
    add_bullet(doc, "Are the sequential links thick or thin? Volatile reputation arcs (thick lines) "
                    "suggest reactive rather than strategic decision-making.")
    add_bullet(doc, "Do the amber cross-causal links connect to your largest nodes? "
                    "If your R5 (Climate Risk) node is large and a dashed line runs from your R3, "
                    "your supply chain choices directly amplified that financial exposure.")
    add_bullet(doc, "What colour is the nebula? If it shifted from green to amber to red across the "
                    "timeline, your reputation was eroding — even if your financials looked healthy.")


# ─────────────────────────────────────────────────────────────────
#  FACILITATOR SECTION  (deeper, with pedagogical rationale)
# ─────────────────────────────────────────────────────────────────
def add_facilitator_section(doc):
    doc.add_page_break()

    add_heading(doc, 'Facilitator Reference: ESG Impact Constellation', level=1)

    add_body(doc,
        "The ESG Impact Constellation is a real-time 3D causal network rendered using React Three Fiber "
        "(WebGL). It transforms the simulation's round-by-round state history into an interactive "
        "knowledge artefact that supports post-game sense-making and debrief facilitation."
    )

    # ── Pedagogical Purpose ──
    add_heading(doc, 'Pedagogical Purpose', level=2)
    add_body(doc,
        "The Constellation operationalises three core learning objectives:"
    )
    add_bullet(doc,
        "Systems Thinking — Players must trace how one decision at Round 1 structurally "
        "constrains or enables decisions at Round 10. The hardcoded cross-causal (amber dashed) "
        "links make these invisible system relationships visible."
    )
    add_bullet(doc,
        "Consequence Awareness — The node size formula (|Treasury Δ| ÷ $5M) creates a direct "
        "embodied representation of financial consequence magnitude. Groups who see one massive "
        "sphere surrounded by tiny ones immediately understand which decision dominated their "
        "financial narrative."
    )
    add_bullet(doc,
        "ESG Integration vs. Silo Thinking — The dimension colour system combined with the "
        "filter bar allows facilitators to demonstrate graphically whether a team treated "
        "Environmental, Social, and Governance as separate concerns or as an integrated whole."
    )

    # ── Technical Architecture ──
    add_heading(doc, 'Technical Architecture', level=2)
    add_body(doc,
        "The component (ESGImpactConstellation.js) receives the full session history array from "
        "the backend on mount. Each round's node is constructed via the buildConstellationData() "
        "function which reads three state deltas per round:"
    )
    add_bullet(doc, "corporate_treasury — Drives node size (magnitude of financial impact)")
    add_bullet(doc, "group_reputation — Drives sequential link thickness and nebula colour")
    add_bullet(doc, "tco2e_emissions — Drives the Carbon Δ tooltip metric (green = reduction)")
    add_body(doc,
        "Nodes are positioned in 3D space using a spiral layout formula (angle derived from "
        "round number × 2.5π, radius expanding linearly) so that later rounds always occupy "
        "the outer arc of the constellation — making chronological progression spatially intuitive."
    )

    # ── Dimension Assignment Logic ──
    add_heading(doc, 'Dimension Assignment Logic', level=2)
    add_body(doc,
        "Each round is pre-assigned to an ESG dimension based on its primary pedagogical content:"
    )

    dim_table = doc.add_table(rows=1, cols=3)
    dim_table.style = 'Table Grid'
    dim_table.rows[0].cells[0].text = 'Dimension'
    dim_table.rows[0].cells[1].text = 'Rounds'
    dim_table.rows[0].cells[2].text = 'Rationale'
    dim_data = [
        ('Environmental (#10b981)', 'R1, R3, R5, R7, R8',
         'Rounds where physical planet boundaries (emissions, water, supply chain carbon, '
         'circular flows, climate scenarios) are the primary decision frame.'),
        ('Social (#3b82f6)', 'R4, R9',
         'Rounds where community impact, worker welfare, and social licence-to-operate '
         'are the dominant ESG stress.'),
        ('Governance (#8b5cf6)', 'R2, R6',
         'Rounds anchored in reporting integrity (Double Materiality) and algorithmic '
         'accountability (AI Ethics).'),
        ('Mixed (#5eead4)', 'R10',
         'The Activist Ultimatum finale tests all three dimensions simultaneously, '
         'reflecting the real-world convergence of ESG pressure at corporate climax events.'),
    ]
    for dim, rounds, rationale in dim_data:
        row = dim_table.add_row()
        row.cells[0].text = dim
        row.cells[1].text = rounds
        row.cells[2].text = rationale

    doc.add_paragraph()

    # ── Cross-Causal Links (Facilitator Detail) ──
    add_heading(doc, 'Hardcoded Cross-Causal Links — Facilitation Notes', level=2)
    add_body(doc,
        "Three systemic causal links are encoded directly in the component. These are not "
        "stochastic — they always appear if the relevant rounds exist in history. "
        "Use them as discussion anchors:"
    )
    add_bullet(doc,
        "R3 → R5 (Scope 3 → Climate Risk, strength 0.6): "
        "Prompt: 'Look at this dashed amber line. Your Scope 3 decisions in Round 3 directly "
        "shaped the climate risk exposure you faced in Round 5. Teams who contracted low-carbon "
        "suppliers in R3 typically see a 15–22% smaller R5 penalty. How does your R5 node compare?'"
    )
    add_bullet(doc,
        "R4 → R7 (ESG Contagion → Circular Economy, strength 0.4): "
        "Prompt: 'The ESG Contagion round is often underestimated. But notice this link — the "
        "social licence you managed (or failed to manage) in R4 determined which Circular Economy "
        "options were available to you in R7. Teams with negative social scores in R4 found "
        "their highest-return circular options blocked.'"
    )
    add_bullet(doc,
        "R1 → R10 (ESG Materiality → Activist Ultimatum, strength 0.8): "
        "Prompt: 'This is the most powerful link in the constellation. The materiality framing you "
        "chose in Round 1 — what you decided was financially material versus what you dismissed — "
        "set the agenda for your entire strategic trajectory. Teams who underweighted climate or "
        "social risks in R1 face a structurally harder R10 ultimatum. What did you prioritise?'"
    )

    # ── Debrief Facilitation Workflow ──
    add_heading(doc, 'Recommended Debrief Facilitation Workflow', level=2)
    add_body(doc,
        "Follow this 4-step protocol when using the Constellation in a group debrief:"
    )
    add_bullet(doc,
        "Step 1 — Full Timeline, All Dimensions (2 min): Open the Constellation for the group "
        "and let everyone observe the full R1–R10 arc together. Ask: 'What is your first "
        "impression? What stands out?'"
    )
    add_bullet(doc,
        "Step 2 — Filter by Dimension (3 min per filter): Cycle through E → S → G filters. "
        "For each filter, ask teams to count their active nodes. A team with 0 social nodes "
        "glowing bright demonstrates a siloed ESG strategy."
    )
    add_bullet(doc,
        "Step 3 — Click the Outlier Node (5 min): Ask each team to identify their single "
        "largest node (the biggest financial shock). Click it to reveal the tooltip. Ask: "
        "'Was this a conscious strategic bet or an unintended consequence?'"
    )
    add_bullet(doc,
        "Step 4 — Trace the Amber Lines (5 min): Walk through the three cross-causal links "
        "using the prompts above. Connect each link to the team's actual numeric outcomes."
    )

    # ── Nebula Interpretation ──
    add_heading(doc, 'Nebula Colour Interpretation Table', level=2)
    neb_table = doc.add_table(rows=1, cols=3)
    neb_table.style = 'Table Grid'
    neb_table.rows[0].cells[0].text = 'Nebula Colour'
    neb_table.rows[0].cells[1].text = 'Reputation Range'
    neb_table.rows[0].cells[2].text = 'Facilitator Interpretation'
    neb_data = [
        ('Green', '≥ 65', 'Team maintained consistent stakeholder trust. ESG messaging was credible.'),
        ('Amber', '40–64', 'Mixed credibility. Some rounds damaged reputation; recovery was partial.'),
        ('Red', '< 40', 'Reputation crisis. Team likely made at least one decision that severed '
                        'social licence. Check R4 (Contagion) and R9 (Just Transition) nodes for culprits.'),
    ]
    for colour, rep, interp in neb_data:
        row = neb_table.add_row()
        row.cells[0].text = colour
        row.cells[1].text = rep
        row.cells[2].text = interp

    doc.add_paragraph()

    # ── Common Misconceptions ──
    add_heading(doc, 'Common Player Misconceptions to Address', level=2)
    add_bullet(doc,
        "\"Bigger nodes are better.\" — Correct this immediately. A large node means a large "
        "financial shock in either direction. A very large node from a costly green investment "
        "may have been wise; a large node from a crisis penalty was not."
    )
    add_bullet(doc,
        "\"The amber lines mean we made mistakes.\" — Clarify that cross-causal links are not "
        "judgements. They are structural system relationships. The line from R1 to R10 exists "
        "regardless of whether R1 was a good or bad decision — it simply shows the system's "
        "long-range memory."
    )
    add_bullet(doc,
        "\"A green nebula means we won.\" — Reputation is one metric. A team can have a green "
        "nebula and still be in financial loss. The Constellation shows the multi-dimensional "
        "nature of the challenge — no single metric tells the full story."
    )


# ─────────────────────────────────────────────────────────────────
#  RUNNER
# ─────────────────────────────────────────────────────────────────
def process(filepath, add_fn, label):
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return

    doc = docx.Document(filepath)
    add_fn(doc)

    name, ext = os.path.splitext(filepath)
    out = f"{name}_with_Constellation{ext}"
    doc.save(out)
    print(f"[OK] {label} saved -> {os.path.basename(out)}")


if __name__ == '__main__':
    process(STUDENT_MANUAL, add_player_section, "Player Manual")
    process(FACILITATOR_MANUAL, add_facilitator_section, "Facilitator Manual")
