"""
update_manuals_csrd.py
Inserts / rewrites the CSRD Double Materiality screen explanation in both
the Student Manual v7 and the Facilitator Manual v7.

Strategy:
  - Locate the paragraph AFTER "3. Mitigation Costs (Issue Chips)" section ends
    (just before 'Section: Single Business Mode' in student; equivalent in fac.)
  - Insert a new Heading 2 + body that covers:
      (a) How the CSRD screen is organised (screen anatomy)
      (b) Complete fund-flow explanation (Q1 budget counter, panel fee, CFO release)
  - Also expand the existing thin Heading 2 bullets with richer text where appropriate.
  - Save as _v8 copies so v7 originals are untouched.
"""

import copy
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, RGBColor
import re

# ── Content to inject ─────────────────────────────────────────────────────────

SCREEN_LAYOUT_HEADING = "4. How the CSRD Screen Is Organised"

SCREEN_LAYOUT_INTRO = (
    "When the CSRD Double Materiality screen opens (Round 2), it replaces the "
    "standard cockpit with a full-screen assessment workspace. Understanding its "
    "three zones will help you work efficiently."
)

SCREEN_LAYOUT_BULLETS = [
    (
        "Zone 1 — Header Bar (top strip): "
        "Shows the session title, a live 'Placed X / Y issues' counter with a "
        "progress bar, the 'Q1 Budget' meter (running total of mitigation costs "
        "for issues you have placed in Quadrant 1 vs. the total CSF pool), and "
        "action buttons (Undo, Reset, Commission Stakeholder Panel Survey, Submit)."
    ),
    (
        "Zone 2 — Left Pane (Issue Bank): "
        "Contains all ESG issue chips waiting to be classified. Each chip shows "
        "the issue title, a category badge (E = Ecological, S = Social, "
        "G = Governance), an ESRS topic tag (e.g., E1, S2), a severity badge "
        "(H / M / L), a time-horizon badge (ST / MT / LT), an IRO badge "
        "(IMP = Impact, RSK = Risk, OPP = Opportunity), and a cost badge "
        "(e.g., $1.2M) showing the mitigation cost that will be charged if "
        "the issue is placed in Q1. "
        "Hover over any chip to read the full issue description. "
        "A Horizon filter (All / ST / MT / LT) lets you focus on issues by "
        "time horizon without removing placed issues from the matrix."
    ),
    (
        "Zone 3 — Right Pane (2x2 Matrix): "
        "The matrix is divided into four quadrants based on two axes: "
        "Financial Materiality (x-axis, left = Low, right = High) and "
        "Impact Materiality / People & Planet (y-axis, bottom = Low, top = High). "
        "Drag chips from the Issue Bank into the quadrant where you judge they belong:\n"
        "  • Q1 (Top Right) — 'CFO Approved — Prioritise & Allocate CapEx': "
        "doubly material issues. Placing an issue here commits its mitigation cost.\n"
        "  • Q2 (Top Left) — 'Monitor & Engage': high impact, low financial risk. "
        "Requires disclosure investment, not capex.\n"
        "  • Q3 (Bottom Right) — 'Watch & Manage': high financial risk, low impact. "
        "Financially material but not ESRS impact-material.\n"
        "  • Q4 (Bottom Left) — 'Low Priority': immaterial on both axes. "
        "Placing 'greenwashing distractor' issues here is good governance."
    ),
    (
        "Submit Button behaviour: "
        "The 'Submit Matrix to CFO' button is disabled until at least 6 issues "
        "have been placed into any quadrant (the minimum for a valid materiality "
        "assessment). It is also disabled if the total Q1 mitigation cost exceeds "
        "your current CSF pool balance. Once enabled, clicking it sends the "
        "assessment to the backend for CFO scoring."
    ),
]

FUND_FLOW_HEADING = "5. How Funds Are Calculated — Step by Step"

FUND_FLOW_INTRO = (
    "The CSRD submission triggers a four-step financial calculation in the backend. "
    "Understanding this helps you make deliberate trade-off decisions."
)

FUND_FLOW_STEPS = [
    (
        "Step 1 — Stakeholder Panel Fee (if commissioned): "
        "If you clicked 'Commission Stakeholder Panel Survey' and chose to "
        "pre-rate N issues, the fee is deducted from corporate treasury "
        "immediately and is non-refundable regardless of matrix accuracy. "
        "Fee schedule: Issues 1–4 cost $250,000 each; Issues 5–8 cost "
        "$500,000 each (the cost doubles above 4 to reflect wider engagement). "
        "Maximum fee (8 issues): $3,000,000. "
        "Example: rating 6 issues = (4 × $250K) + (2 × $500K) = $2,000,000."
    ),
    (
        "Step 2 — CFO Validation Gate: "
        "The backend checks whether every issue you placed in Q1 (Top Right) "
        "is genuinely doubly material. An issue is doubly material if its "
        "severity_score × likelihood_score is ≥ 12 out of 25 on both the "
        "financial and societal axes (ESRS 1 §1.51 threshold). "
        "If any Q1 issue fails this test and you have not chosen the CFO "
        "Override, the submission is rejected with an error message — "
        "review your Q1 placements and resubmit. "
        "If you choose the CFO Override, the submission proceeds but "
        "Group Reputation is reduced by −10 points."
    ),
    (
        "Step 3 — Accuracy Scoring & Capital Release (M_acc): "
        "The backend counts how many of the true Q1 issues (those that "
        "genuinely meet the ≥ 12/25 threshold on both axes) you correctly "
        "placed in Q1, then divides by the total number of true Q1 issues:\n"
        "  M_acc = Correct Q1 placements ÷ Total true Q1 issues\n"
        "The CFO then releases:\n"
        "  Allocated Budget = $15,000,000 × M_acc\n"
        "Example: if 5 of 6 true Q1 issues were correctly placed, "
        "M_acc = 83.3%, and the CFO releases $12,500,000. "
        "Partial credit is awarded for 'ambiguous' issues placed in "
        "adjacent quadrants (e.g., a borderline Q1/Q2 issue placed in Q2 "
        "earns 0.5 credit). "
        "Note: the allocated budget is a capital commitment — it is "
        "deducted from your corporate treasury, not added to it."
    ),
    (
        "Step 4 — Option C Clawback (if applicable): "
        "If you chose Option C (Ignore the Materiality Framework) in the "
        "Round 2 governance decision, the backend applies a 40% clawback "
        "to the allocated budget before deducting it. This models the "
        "governance principle that capital cannot be released for ESG "
        "programmes if the board has simultaneously decided to ignore the "
        "ESG framework. "
        "Example: $12,500,000 × 40% clawback = $5,000,000 forfeited, "
        "leaving a net commitment of $7,500,000."
    ),
    (
        "Bonus — Q2 Disclosure Budget: "
        "For every Q2 issue (High Impact / Low Financial) you correctly "
        "place in Q2 that carries a 'disclosure_required' flag, the system "
        "pro-rates a share of the $1,000,000 Disclosure Investment Budget. "
        "This is a separate allocation for data collection, assurance, and "
        "stakeholder engagement costs (not capex). It is not deducted from "
        "the $15M pool."
    ),
    (
        "Accuracy Bonus: "
        "If your overall placement accuracy across all four quadrants reaches "
        "≥ 80%, you receive a 1,000-point bonus to your simulation score "
        "(this is a learning bonus, not a financial figure)."
    ),
]

FUND_SUMMARY_HEADING = "Summary: The Q1 Budget Counter vs. the CFO Allocation"

FUND_SUMMARY_BODY = (
    "The 'Q1 Budget' counter you see in the header bar while building your "
    "matrix is NOT the amount the CFO will release. It is the sum of the "
    "mitigation costs of issues you have placed in Q1 — a running cost "
    "estimate that tells you whether your selections are affordable within "
    "your CSF pool. "
    "The actual capital committed at submission is calculated by the backend "
    "based on accuracy (M_acc × $15M), independent of the individual chip "
    "costs. The chip costs are the 'price tags' on mitigation programmes; "
    "the $15M × M_acc is the CFO's governance-based budget release."
)

# ── Facilitator-specific additions ────────────────────────────────────────────

FAC_DEBRIEF_HEADING = "6. Facilitator Debrief Prompts — CSRD Screen"

FAC_DEBRIEF_BULLETS = [
    (
        "Screen literacy first: Before asking strategic questions, confirm that "
        "all players understood the two-axis logic (financial vs. impact). "
        "Ask: 'Which axis did you find harder to judge — financial risk or "
        "societal impact? Why?' This surfaces system-1 vs. system-2 reasoning."
    ),
    (
        "The panel fee trade-off: The stakeholder panel reduces uncertainty but "
        "costs up to $3M. Ask: 'Did commissioning the panel change any of your "
        "placements? Was the fee worth the accuracy improvement?' This teaches "
        "the real ESRS §1.47-1.50 stakeholder engagement cost-benefit."
    ),
    (
        "Q1 vs. Q2 confusion is a feature: Many players will place Q2 issues "
        "(living wage, philanthropy) in Q1 because they seem morally important. "
        "This triggers the CFO rejection gate. Use this moment to explain: "
        "'The CSRD distinguishes between what requires capital allocation "
        "(Q1) and what requires disclosure investment (Q2). Both matter, "
        "but they are funded differently.'"
    ),
    (
        "Option C clawback reveal: If any team chose Option C in the governance "
        "decision, the 40% clawback will appear in their debrief card. "
        "Point to the numbers explicitly: 'Your governance posture retroactively "
        "reduced the capital your materiality work could release. This is how "
        "real boards experience ESG inconsistency.'"
    ),
    (
        "Accuracy scoring transparency: The backend stores a per-issue score "
        "breakdown (severity × likelihood product, correct quadrant, placed "
        "quadrant, credit awarded). You can access this in the admin dashboard "
        "under Session → ESRS Debrief. Share it with teams in debrief to show "
        "exactly which placements cost or saved them capital."
    ),
    (
        "ESRS Assurance Readiness rating: At the end of CSRD scoring, each team "
        "receives a 0–4 star ESRS Assurance Readiness rating based on four "
        "signals: Q1 recall ≥ 80%, board governance choice (not Option C), "
        "Q2 issues correctly disclosed, and ambiguous issues handled thoughtfully. "
        "Show this rating in debrief as a proxy for real-world external assurance "
        "eligibility under ISAE 3000."
    ),
]

# ── Helper functions ───────────────────────────────────────────────────────────

def add_heading(doc, text, level):
    """Add a heading paragraph at the given level."""
    p = doc.add_heading(text, level=level)
    return p

def add_body(doc, text):
    """Add a normal paragraph."""
    p = doc.add_paragraph(text)
    p.style = doc.styles['Normal']
    return p

def add_bullet(doc, text):
    """Add a list bullet paragraph."""
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(text)
    return p

def insert_paragraphs_after(doc, anchor_para_index, new_paragraphs):
    """
    Insert a list of (style, text) tuples into doc after anchor_para_index.
    new_paragraphs: list of ('heading1'|'heading2'|'heading3'|'normal'|'bullet', text)
    """
    # We need to insert XML elements after the anchor paragraph's XML element
    anchor_xml = doc.paragraphs[anchor_para_index]._element
    parent = anchor_xml.getparent()

    # Build new XML paragraphs in reverse order so each is inserted right after anchor
    for style_key, text in reversed(new_paragraphs):
        new_para = OxmlElement('w:p')

        # Paragraph properties
        pPr = OxmlElement('w:pPr')
        pStyle = OxmlElement('w:pStyle')

        style_map = {
            'heading1': 'Heading1',
            'heading2': 'Heading2',
            'heading3': 'Heading3',
            'normal': 'Normal',
            'bullet': 'ListBullet',
        }
        # Map to the actual style ID in the doc
        style_id = {
            'heading1': 'Heading1',
            'heading2': 'Heading2',
            'heading3': 'Heading3',
            'normal': 'Normal',
            'bullet': 'ListBullet',
        }.get(style_key, 'Normal')

        pStyle.set(qn('w:val'), style_id)
        pPr.append(pStyle)
        new_para.append(pPr)

        # Run with text
        r = OxmlElement('w:r')
        t = OxmlElement('w:t')
        t.text = text
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        r.append(t)
        new_para.append(r)

        # Insert immediately after anchor
        anchor_xml.addnext(new_para)


def build_new_content_student():
    """Returns list of (style, text) for student manual insertion."""
    content = []

    # ── Section 4: Screen organisation ────────────────────────────────────────
    content.append(('heading2', SCREEN_LAYOUT_HEADING))
    content.append(('normal', SCREEN_LAYOUT_INTRO))
    for bullet in SCREEN_LAYOUT_BULLETS:
        content.append(('bullet', bullet))

    # ── Section 5: Fund calculation ────────────────────────────────────────────
    content.append(('heading2', FUND_FLOW_HEADING))
    content.append(('normal', FUND_FLOW_INTRO))
    for step in FUND_FLOW_STEPS:
        content.append(('bullet', step))

    # ── Summary box ───────────────────────────────────────────────────────────
    content.append(('heading3', FUND_SUMMARY_HEADING))
    content.append(('normal', FUND_SUMMARY_BODY))

    return content


def build_new_content_facilitator():
    """Returns list of (style, text) for facilitator manual insertion."""
    content = build_new_content_student()   # same base content

    # ── Section 6: Facilitator debrief prompts ────────────────────────────────
    content.append(('heading2', FAC_DEBRIEF_HEADING))
    for bullet in FAC_DEBRIEF_BULLETS:
        content.append(('bullet', bullet))

    return content


def find_anchor_index(doc, search_text):
    """Find the index of the last paragraph whose text starts with search_text."""
    result = None
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip().startswith(search_text):
            result = i
    return result


# ── Process Student Manual ────────────────────────────────────────────────────
print("Processing Student Manual v7...")
doc_s = Document(r'Muressons_Student_Manual_v7.docx')

# Find the end of the existing appendix: last bullet in section 3 (Mitigation Costs)
# We look for the paragraph "Prioritise Budget: The sum..." then insert after it
anchor_s = find_anchor_index(doc_s, 'Prioritise Budget')
if anchor_s is None:
    # Fallback: find end of section 3 heading
    anchor_s = find_anchor_index(doc_s, '3. Mitigation Costs')
print(f"  Student: inserting after para index {anchor_s}: '{doc_s.paragraphs[anchor_s].text[:60]}'")

insert_paragraphs_after(doc_s, anchor_s, build_new_content_student())

doc_s.save(r'Muressons_Student_Manual_v8.docx')
print("  Saved: Muressons_Student_Manual_v8.docx")


# ── Process Facilitator Manual ────────────────────────────────────────────────
print("Processing Facilitator Manual v7...")
doc_f = Document(r'Muressons_Facilitator_Manual_v7.docx')

anchor_f = find_anchor_index(doc_f, 'Prioritise Budget')
if anchor_f is None:
    anchor_f = find_anchor_index(doc_f, '3. Mitigation Costs')
print(f"  Facilitator: inserting after para index {anchor_f}: '{doc_f.paragraphs[anchor_f].text[:60]}'")

insert_paragraphs_after(doc_f, anchor_f, build_new_content_facilitator())

doc_f.save(r'Muressons_Facilitator_Manual_v8.docx')
print("  Saved: Muressons_Facilitator_Manual_v8.docx")

print("\nDone. Both v8 files written.")
