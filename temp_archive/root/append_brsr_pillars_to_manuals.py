"""
append_brsr_pillars_to_manuals.py
---------------------------------
Appends the BRSR Strategic Pillars section (with screenshots) to:
  - Muressons_Student_Manual_v6.docx              (Player Manual)
  - Muressons_Facilitator_Manual_v6.docx           (Facilitator Manual)

Outputs versioned copies:
  - Muressons_Student_Manual_v7.docx
  - Muressons_Facilitator_Manual_v7.docx
"""

import os
import docx
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE_DIR = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim"
IMG_DIR = os.path.join(BASE_DIR, "guide_images")

STUDENT_MANUAL = os.path.join(BASE_DIR, "Muressons_Student_Manual_v6.docx")
FACILITATOR_MANUAL = os.path.join(BASE_DIR, "Muressons_Facilitator_Manual_v6.docx")

# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────
def add_heading(doc, text, level=1):
    doc.add_heading(text, level=level)

def add_body(doc, text):
    p = doc.add_paragraph(text)
    p.style.font.size = Pt(11)
    return p

def add_bold_body(doc, bold_text, normal_text=""):
    p = doc.add_paragraph()
    run = p.add_run(bold_text)
    run.bold = True
    run.font.size = Pt(11)
    if normal_text:
        run2 = p.add_run(normal_text)
        run2.font.size = Pt(11)
    return p

def add_bullet(doc, text):
    doc.add_paragraph(text, style='List Bullet')

def add_image(doc, filename, width_inches=5.5, caption=None):
    """Add an image from guide_images/ with optional caption."""
    img_path = os.path.join(IMG_DIR, filename)
    if os.path.exists(img_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(img_path, width=Inches(width_inches))
        if caption:
            cap = doc.add_paragraph(caption)
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap.style.font.size = Pt(9)
            cap.style.font.color.rgb = RGBColor(148, 163, 184)
    else:
        doc.add_paragraph(f"[Image: {filename} — not found at {img_path}]")

def add_table_header(table, *headers):
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = h

def add_table_row(table, *values):
    row = table.add_row()
    for i, v in enumerate(values):
        if i < len(row.cells):
            row.cells[i].text = str(v)


# ═════════════════════════════════════════════════════════════════
#  PLAYER SECTION  (Student Manual)
# ═════════════════════════════════════════════════════════════════
def add_player_section(doc):
    doc.add_page_break()

    # ── Title ──
    add_heading(doc, "Section: BRSR Strategic Pillars — India Compliance Pathway", level=1)

    add_body(doc,
        "The BRSR (Business Responsibility and Sustainability Reporting) Strategic Pillars mode "
        "transforms the Muressons simulation into a focused 10-round Indian regulatory compliance "
        "experience. Your executive team navigates "
        "the Securities and Exchange Board of India (SEBI) mandate for BRSR reporting, making "
        "granular decisions across five strategic areas every round."
    )

    add_body(doc,
        "This mode is designed for students studying Indian corporate governance, "
        "sustainability reporting under the Companies Act 2013, and the nine NGRBC "
        "(National Guidelines on Responsible Business Conduct) principles."
    )

    # ── How It Differs ──
    add_heading(doc, "How BRSR Mode Differs from Standard Play", level=2)

    tbl = doc.add_table(rows=1, cols=3)
    tbl.style = 'Table Grid'
    add_table_header(tbl, "Feature", "Standard Mode (10 rounds)", "BRSR Mode (10 rounds)")
    add_table_row(tbl, "Rounds", "10", "10")
    add_table_row(tbl, "Currency", "USD ($)", "Indian Rupee (₹)")
    add_table_row(tbl, "Decision Format", "Option A / B / C", "5 Strategic Pillars × 3 options each")
    add_table_row(tbl, "Round Themes", "Global ESG topics", "SEBI NGRBC Principles (P1–P9)")
    add_table_row(tbl, "Regulatory Bodies", "Generic regulators", "SEBI, CPCB, CRISIL, MCA")
    add_table_row(tbl, "End-Game Certificate", "Archetype profile", "SBRI Certificate with NGRBC audit")
    add_table_row(tbl, "Terminal Multiplier", "Base M_R", "M_R + BRSR compliance bonus/penalty")

    doc.add_paragraph()  # spacer

    # ── The Five Strategic Pillars ──
    add_heading(doc, "The Five Strategic Pillars", level=2)

    add_body(doc,
        "Every round, you make independent decisions across five strategic areas. "
        "Each area offers three options ranging from ambitious Leadership Indicators "
        "(highest cost, highest impact) to Essential Indicators (moderate) to Status Quo "
        "(zero cost, but increased regulatory risk)."
    )

    add_image(doc, "brsr_pillar_tiles.png", width_inches=5.5,
              caption="Figure: The 5 Strategic Pillar tiles with 3 options each")

    pillar_table = doc.add_table(rows=1, cols=3)
    pillar_table.style = 'Table Grid'
    add_table_header(pillar_table, "Pillar", "Icon", "What It Covers")
    add_table_row(pillar_table, "Energy", "⚡",
                  "Board governance, ESG committees, OHS upgrades, energy systems, integrated reporting")
    add_table_row(pillar_table, "Operations", "🏭",
                  "Transparency registers, POSH remediation, EPR compliance, assurance standards, dashboards")
    add_table_row(pillar_table, "Supply Chain", "🔗",
                  "Value chain ethics, human rights due diligence, waste partnerships, supplier development, GRI mapping")
    add_table_row(pillar_table, "Offsetting", "🌿",
                  "Ethics boards, living wage funds, SBTi pathways, consumer analytics, materiality validation")
    add_table_row(pillar_table, "Human Resources", "👥",
                  "Whistleblower hotlines, DEI dashboards, green skills academies, supplier ESG training, analyst packs")

    doc.add_paragraph()

    # ── Round-by-Round Guide ──
    add_heading(doc, "Round-by-Round NGRBC Principle Map", level=2)

    round_table = doc.add_table(rows=1, cols=4)
    round_table.style = 'Table Grid'
    add_table_header(round_table, "Round", "Theme", "NGRBC Principles", "Key Decision")
    add_table_row(round_table, "R1", "Governance & Transparency", "P1, P7",
                  "Board ESG committee vs. ethics audit vs. status quo")
    add_table_row(round_table, "R2", "Workforce & Human Rights", "P3, P5",
                  "ISO 45001 OHS upgrade vs. basic compliance vs. no change")
    add_table_row(round_table, "R3", "Environment & Circularity", "P6, P2",
                  "ZLD for pharma plants vs. water recycling vs. no change")
    add_table_row(round_table, "R4", "Value Chain & BRSR Core", "P4, P8, P9",
                  "Big 4 reasonable assurance vs. limited assurance vs. self-assessment")
    add_table_row(round_table, "R5", "Integrated Disclosure", "All",
                  "Six Capitals integrated report vs. strategic KPIs vs. minimal filing")

    doc.add_paragraph()

    # ── Costs in Indian Rupees ──
    add_heading(doc, "Understanding Costs in ₹ (Indian Rupees)", level=2)

    add_body(doc,
        "All costs in BRSR mode are denominated in Indian Rupees and scaled for a large Indian "
        "conglomerate. Here is a rough guide to the cost tiers:"
    )

    cost_table = doc.add_table(rows=1, cols=3)
    cost_table.style = 'Table Grid'
    add_table_header(cost_table, "Option Tier", "Cost per Area", "Total per Round (5 areas)")
    add_table_row(cost_table, "Leadership (Option A)", "₹15–30 Lakh", "₹80 Lakh – ₹1 Crore")
    add_table_row(cost_table, "Essential (Option B)", "₹4–12 Lakh", "₹30–50 Lakh")
    add_table_row(cost_table, "Status Quo (Option C)", "₹0", "₹0")

    doc.add_paragraph()
    add_body(doc,
        "Note: ₹1 Crore = ₹100 Lakh = ₹10,000,000. Choosing Leadership options across all 5 "
        "areas will cost approximately ₹80 Lakh to ₹1 Crore per round — a significant but "
        "strategically rewarding investment."
    )

    # ── Regulatory Penalties ──
    add_heading(doc, "Regulatory Penalties — What Happens If You Cut Corners", level=2)

    add_body(doc,
        "Unlike the standard mode, BRSR mode simulates real Indian regulatory enforcement. "
        "Choosing Status Quo options triggers penalties from actual regulatory bodies:"
    )

    add_image(doc, "brsr_regulatory_penalties.png", width_inches=5.0,
              caption="Figure: BRSR regulatory consequences by round")

    penalty_table = doc.add_table(rows=1, cols=4)
    penalty_table.style = 'Table Grid'
    add_table_header(penalty_table, "Round", "Trigger", "Consequence", "Amount")
    add_table_row(penalty_table, "R3", "Regulatory Minimum chosen",
                  "CPCB API discharge penalty — direct treasury deduction", "₹50 Lakh")
    add_table_row(penalty_table, "R4", "Self-Assessment (no assurance)",
                  "SEBI show-cause notice — greenwash crisis + treasury penalty", "₹1 Crore")
    add_table_row(penalty_table, "R5", "Compliance-only filing",
                  "Green Bond rating downgrade — NCD interest rate +1.5%", "Ongoing")
    add_table_row(penalty_table, "R5", "Integrated Report (score ≥ 70)",
                  "CRISIL AAA Green Bond discount — NCD interest rate −1.5%", "Ongoing reward")

    doc.add_paragraph()

    # ── Terminal Valuation ──
    add_heading(doc, "Terminal Valuation — The M_R BRSR Bonus", level=2)

    add_body(doc,
        "At the end of Round 10, your BRSR compliance score directly impacts the "
        "Regenerative Multiple (M_R) that determines your terminal valuation:"
    )

    add_image(doc, "brsr_mr_breakdown.png", width_inches=5.0,
              caption="Figure: M_R breakdown showing BRSR steward bonus")

    mr_table = doc.add_table(rows=1, cols=3)
    mr_table.style = 'Table Grid'
    add_table_header(mr_table, "BRSR Score", "M_R Impact", "Label")
    add_table_row(mr_table, "≥ 85", "+0.65", "BRSR Pioneer Bonus")
    add_table_row(mr_table, "≥ 70", "+0.35", "BRSR Steward Bonus")
    add_table_row(mr_table, "40–69", "No bonus/penalty", "Neutral")
    add_table_row(mr_table, "< 40", "−0.30", "BRSR Laggard Penalty")

    doc.add_paragraph()

    add_body(doc,
        "Additionally, achieving a BRSR score of ≥ 80 unlocks the ESG Alpha Dividend, "
        "a permanent +0.05 bonus to M_R. Combined with the Pioneer Bonus, an "
        "exemplary BRSR team can achieve an M_R uplift of +0.70 — a massive advantage "
        "in terminal valuation."
    )

    # ── SBRI Certificate ──
    add_heading(doc, "The SEBI Business Responsibility Index (SBRI) Certificate", level=2)

    add_body(doc,
        "When the simulation ends after Round 10, your team receives an SBRI Certificate — "
        "a comprehensive scorecard that grades your BRSR compliance journey:"
    )

    add_image(doc, "brsr_sbri_certificate.png", width_inches=4.5,
              caption="Figure: SBRI Certificate showing grade, archetype, and NGRBC audit")

    add_bullet(doc,
        "Grade (A+ to F) — Based on your weighted BRSR score across 5 dimensions: "
        "Governance Ethics (20%), Human Capital (20%), Environmental (25%), "
        "Value Chain (20%), Reporting Quality (15%).")
    add_bullet(doc,
        "Archetype — 'BRSR Pioneer' (score ≥ 80), 'Responsible Steward' (≥ 60), "
        "'Compliance Pragmatist' (≥ 40), or 'Regulatory Laggard' (< 40).")
    add_bullet(doc,
        "NGRBC Principle Audit — A 5-column grid showing whether you passed (✅) or "
        "failed (❌) each NGRBC principle cluster across all 5 rounds.")

    # ── Strategy Tips ──
    add_heading(doc, "Strategic Tips for BRSR Mode", level=2)

    add_bullet(doc,
        "Budget across all 5 pillars. Choosing Leadership in Energy but Status Quo in "
        "HR creates a lopsided BRSR profile. SEBI assesses all nine principles holistically.")
    add_bullet(doc,
        "Round 1 governance choices compound. 'Governance Fragility' from R1 triggers "
        "a Whistleblower Crisis in R5 — a ₹ treasury bleed you cannot undo.")
    add_bullet(doc,
        "Round 4 is the assurance cliff. Self-assessment (no third-party assurance) "
        "triggers SEBI greenwash allegations, a ₹1 Crore penalty, and auditor hostility "
        "that persists into the terminal valuation.")
    add_bullet(doc,
        "The ESG Alpha Dividend requires score ≥ 80. This typically means choosing "
        "Leadership or Essential options in most areas across most rounds. Pure Status Quo "
        "play will not reach this threshold.")
    add_bullet(doc,
        "CRISIL AAA discount is earned, not given. Only teams with a BRSR score ≥ 70 who "
        "also file an Integrated Report in R5 receive the Green Bond interest rate discount.")


# ═════════════════════════════════════════════════════════════════
#  FACILITATOR SECTION
# ═════════════════════════════════════════════════════════════════
def add_facilitator_section(doc):
    doc.add_page_break()

    add_heading(doc, "Facilitator Module: BRSR Strategic Pillars — India Compliance Pathway", level=1)

    add_body(doc,
        "The BRSR Strategic Pillars mode is a purpose-built, 10-round simulation pathway "
        "designed for Indian B-school and executive education contexts. It reframes the "
        "entire Muressons decision architecture around the SEBI BRSR mandate and the nine "
        "NGRBC principles, using Indian Rupee costs, Indian regulatory bodies (SEBI, CPCB, "
        "CRISIL, MCA), and Indian-specific compliance consequences."
    )

    # ── Pedagogical Design ──
    add_heading(doc, "Pedagogical Design Intent", level=2)

    add_body(doc, "This module operationalises four learning objectives:")

    add_bullet(doc,
        "Essential vs. Leadership Indicator Fluency — Students must distinguish between "
        "SEBI's mandatory Essential Indicators and voluntary Leadership Indicators across "
        "all nine NGRBC principles. The 5-pillar decision format forces explicit trade-off "
        "reasoning in every area.")
    add_bullet(doc,
        "Regulatory Consequence Awareness — Real Indian penalties (CPCB discharge fines, "
        "SEBI show-cause notices, CRISIL rating impacts) are modelled with realistic ₹ amounts. "
        "Students experience the financial materiality of regulatory non-compliance.")
    add_bullet(doc,
        "Integrated Reporting Competence — Round 5 forces students to confront the "
        "choice between a Six Capitals Integrated Report (GRI/TCFD aligned) and "
        "a minimal compliance filing, with direct M_R and Green Bond consequences.")
    add_bullet(doc,
        "Long-Tail Governance Risk — The 'Governance Fragility' flag mechanism demonstrates "
        "how early governance decisions compound over time, culminating in a Whistleblower "
        "Crisis in R5 that bleeds treasury and governance risk score.")

    # ── Technical Architecture ──
    add_heading(doc, "Technical Architecture", level=2)

    add_body(doc,
        "The BRSR mode uses the same pillar-based decision UI as the standard 'multi_toggles' "
        "paradigm but routes through a dedicated BRSR configuration and aggregation pipeline:"
    )

    arch_table = doc.add_table(rows=1, cols=3)
    arch_table.style = 'Table Grid'
    add_table_header(arch_table, "Component", "File", "Role")
    add_table_row(arch_table, "Pillar Config",
                  "configs.py", "75 options (5 rounds × 5 areas × 3 tiers) with INR costs and NGRBC flags")
    add_table_row(arch_table, "Aggregation",
                  "configs.py", "aggregate_brsr_pillar_decisions() sums costs/impacts/flags across 5 pillars")
    add_table_row(arch_table, "Legacy Translation",
                  "configs.py", "translate_brsr_pillars_to_legacy_choice() maps to option_a/b/c for track.py")
    add_table_row(arch_table, "Router",
                  "router.py", "Routes BRSR paradigm to dedicated aggregation; caps at 5 rounds")
    add_table_row(arch_table, "Consequences",
                  "brsr_controller.py", "Round-specific state mutations, CPCB/SEBI penalties, NCD rate changes")
    add_table_row(arch_table, "Terminal Valuation",
                  "round_logic.py", "M_R scaling based on BRSR compliance score (±0.30 to +0.65)")
    add_table_row(arch_table, "Track Scoring",
                  "track.py", "5-dimension weighted score: GE 20%, HC 20%, EN 25%, VC 20%, RQ 15%")

    doc.add_paragraph()

    # ── Decision Pillar Architecture ──
    add_heading(doc, "Decision Pillar Architecture — 5 Rounds × 5 Areas", level=2)

    add_image(doc, "brsr_pillar_tiles.png", width_inches=5.5,
              caption="Figure: The 5 Strategic Pillar tiles as seen by students")

    add_body(doc,
        "Each round maps to specific NGRBC principles. The pillar options are thematically "
        "aligned but allow students to mix Leadership and Status Quo choices across areas, "
        "creating nuanced compliance profiles rather than binary 'all-in or all-out' strategies."
    )

    round_detail_table = doc.add_table(rows=1, cols=5)
    round_detail_table.style = 'Table Grid'
    add_table_header(round_detail_table, "Round", "Theme", "Principles", "Key Flag (Leadership)", "Key Flag (Status Quo)")
    add_table_row(round_detail_table, "R1", "Governance & Transparency", "P1, P7",
                  "brsr_pioneer", "governance_fragility")
    add_table_row(round_detail_table, "R2", "Workforce & Human Rights", "P3, P5",
                  "brsr_living_wage", "brsr_statutory_minimums")
    add_table_row(round_detail_table, "R3", "Environment & Circularity", "P6, P2",
                  "brsr_circular_symbiosis", "brsr_regulatory_minimum")
    add_table_row(round_detail_table, "R4", "Value Chain & BRSR Core", "P4, P8, P9",
                  "brsr_core_assured", "brsr_greenwash_risk")
    add_table_row(round_detail_table, "R5", "Integrated Disclosure", "All",
                  "brsr_integrated_report", "brsr_compliance_only")

    doc.add_paragraph()

    # ── Regulatory Consequences ──
    add_heading(doc, "Regulatory Consequences — Facilitator Reference", level=2)

    add_body(doc,
        "These consequences fire automatically based on student choices. Use them as "
        "debriefing anchors to illustrate the financial materiality of regulatory non-compliance "
        "in the Indian context."
    )

    add_image(doc, "brsr_regulatory_penalties.png", width_inches=5.0,
              caption="Figure: BRSR regulatory consequence cards")

    add_heading(doc, "R3: CPCB API Discharge Penalty", level=3)
    add_body(doc,
        "Trigger: Student selects 'Regulatory Minimum' (Status Quo) in Round 3 across "
        "environmental pillars. Effect: ₹50 Lakh (₹5,000,000) direct treasury deduction + "
        "NCD interest rate +1% hike. Pedagogical point: The Central Pollution Control Board (CPCB) "
        "has the authority to impose penalties for Active Pharmaceutical Ingredient (API) "
        "discharge violations under the Water (Prevention and Control of Pollution) Act, 1974.")

    add_heading(doc, "R4: SEBI Reasonable Assurance Penalty", level=3)
    add_body(doc,
        "Trigger: Student selects 'Self-Assessment' (no external assurance) in Round 4. "
        "Effect: ₹1 Crore (₹10,000,000) treasury deduction + SEBI greenwash show-cause notice + "
        "auditor tolerance set to 'Hostile'. Pedagogical point: SEBI's BRSR Core framework requires "
        "reasonable assurance for listed companies. Self-assessment without third-party verification "
        "exposes Scope 3 claims to challenge.")

    add_heading(doc, "R5: Green Bond Rating Impact", level=3)
    add_body(doc,
        "Two opposing outcomes in Round 5:\n\n"
        "• Compliance-Only Filing → Green Bond rating downgrade, NCD interest +1.5%. "
        "Illustrates how thin filings erode investor confidence in ESG bond covenants.\n\n"
        "• Integrated Report (score ≥ 70) → CRISIL AAA Green Bond discount, NCD interest −1.5%. "
        "Illustrates how robust integrated disclosure creates capital cost advantages.")

    # ── M_R Terminal Scaling ──
    add_heading(doc, "Terminal Valuation: M_R BRSR Score Scaling", level=2)

    add_image(doc, "brsr_mr_breakdown.png", width_inches=5.0,
              caption="Figure: M_R breakdown with BRSR compliance bonus")

    add_body(doc,
        "The M_R terminal multiplier includes a BRSR-specific scaling component that rewards "
        "consistent compliance and penalises regulatory laggards:"
    )

    mr_fac_table = doc.add_table(rows=1, cols=4)
    mr_fac_table.style = 'Table Grid'
    add_table_header(mr_fac_table, "Score Range", "M_R Delta", "Label", "Typical Profile")
    add_table_row(mr_fac_table, "≥ 85", "+0.65", "Pioneer Bonus",
                  "Leadership choices in 4+ of 5 areas across all rounds")
    add_table_row(mr_fac_table, "≥ 70", "+0.35", "Steward Bonus",
                  "Mix of Leadership and Essential across most rounds")
    add_table_row(mr_fac_table, "40–69", "0", "Neutral",
                  "Mixed profile with some Status Quo rounds")
    add_table_row(mr_fac_table, "< 40", "−0.30", "Laggard Penalty",
                  "Predominantly Status Quo — regulatory non-compliance")

    doc.add_paragraph()

    add_bold_body(doc,
        "Facilitator Tip: ",
        "The difference between Pioneer (+0.65) and Laggard (−0.30) is 0.95× on the "
        "terminal multiplier. For a typical EBITDA of ₹50 Crore with a 12× exit multiple, "
        "this translates to a terminal value swing of approximately ₹570 Crore. Use this "
        "number in debrief to concretise the financial materiality of BRSR compliance.")

    # ── SBRI Certificate ──
    add_heading(doc, "SBRI Certificate — End-Game Artefact", level=2)

    add_image(doc, "brsr_sbri_certificate.png", width_inches=4.5,
              caption="Figure: SBRI Certificate as displayed in GameOverSummary")

    add_body(doc,
        "The SEBI Business Responsibility Index (SBRI) Certificate is displayed after "
        "the final round. It provides a comprehensive view of the team's BRSR journey:"
    )

    add_bullet(doc, "Grade Badge — A+, A, B, C, D, or F with dynamic colour coding")
    add_bullet(doc, "Archetype Title — BRSR Pioneer, Responsible Steward, Compliance Pragmatist, or Regulatory Laggard")
    add_bullet(doc, "Compliance Score — Weighted score out of 100")
    add_bullet(doc,
        "NGRBC Principle Audit Grid — 5-column visual showing pass/fail for each principle "
        "cluster (P1/P7, P3/P5, P6/P2, P4/P8/P9, Integrated Disclosure)")

    add_bold_body(doc,
        "Debrief Suggestion: ",
        "Project the SBRI Certificate for each team side by side. Ask teams to identify "
        "which NGRBC principle cluster they failed (❌) and trace back to the specific round "
        "and pillar choice that caused the failure. This creates a powerful 'decision archaeology' "
        "exercise.")

    # ── Scoring Dimensions ──
    add_heading(doc, "BRSR Scoring Dimensions — Weighted Formula", level=2)

    add_body(doc,
        "The BRSR compliance score is a weighted average of five dimensions, each mapped to "
        "specific NGRBC principles:"
    )

    dim_table = doc.add_table(rows=1, cols=4)
    dim_table.style = 'Table Grid'
    add_table_header(dim_table, "Dimension", "Weight", "NGRBC Principles", "Driven By")
    add_table_row(dim_table, "Governance Ethics", "20%", "P1, P7",
                  "R1 pillar choices (board ESG committee, lobbying register, ethics training)")
    add_table_row(dim_table, "Human Capital", "20%", "P3, P5",
                  "R2 pillar choices (ISO 45001, POSH remediation, DEI dashboard)")
    add_table_row(dim_table, "Environmental", "25%", "P6, P2",
                  "R3 pillar choices (ZLD, EPR compliance, SBTi pathway)")
    add_table_row(dim_table, "Value Chain", "20%", "P4, P8, P9",
                  "R4 pillar choices (blockchain traceability, Big 4 assurance, MSME development)")
    add_table_row(dim_table, "Reporting Quality", "15%", "All",
                  "R5 pillar choices (Six Capitals report, ESG-financial dashboard, GRI/TCFD mapping)")

    doc.add_paragraph()

    add_body(doc,
        "Score = GE×0.20 + HC×0.20 + EN×0.25 + VC×0.20 + RQ×0.15. "
        "Each dimension scores 0–100 based on the tier of options selected in the corresponding round. "
        "Leadership options set the dimension to 80; Essential to ~50; Status Quo to ~5."
    )

    # ── Debrief Protocol ──
    add_heading(doc, "Recommended Debrief Protocol for BRSR Mode", level=2)

    add_body(doc, "Follow this 5-step protocol after the simulation concludes:")

    add_bullet(doc,
        "Step 1 — Certificate Reveal (3 min): Display each team's SBRI Certificate. "
        "Let them absorb their grade and archetype before discussion begins.")
    add_bullet(doc,
        "Step 2 — Principle Audit Walk (5 min): Go column by column through the "
        "NGRBC audit grid. For each ❌, ask the team: 'What did you choose in this round, "
        "and why?' This surfaces the decision rationale that led to non-compliance.")
    add_bullet(doc,
        "Step 3 — Penalty Impact Analysis (5 min): Ask teams who received CPCB or SEBI "
        "penalties to calculate what percentage of their final treasury was lost to "
        "regulatory fines. Compare against the cost of compliance they chose to avoid.")
    add_bullet(doc,
        "Step 4 — M_R Multiplier Discussion (5 min): Display the M_R breakdown. "
        "Ask: 'If you could replay one round with a different choice in one pillar, "
        "which would it be and how would it change your terminal value?'")
    add_bullet(doc,
        "Step 5 — Real-World Connection (5 min): Ask students to name one Indian "
        "company that has faced a SEBI show-cause notice or CPCB penalty in the last "
        "2 years. Connect the simulation experience to real regulatory enforcement.")

    # ── Facilitator Controls ──
    add_heading(doc, "Facilitator Controls & Configuration", level=2)

    add_body(doc,
        "To activate BRSR mode, select 'BRSR / NGRBC' as the decision paradigm when "
        "creating a session (solo-start or facilitator cohort creation). The system will "
        "automatically:"
    )

    add_bullet(doc, "Set currency to Indian Rupee (₹)")
    add_bullet(doc, "Load BRSR-specific pillar options for each round")
    add_bullet(doc, "Route pillar decisions through the BRSR aggregation pipeline")
    add_bullet(doc, "Apply Indian regulatory penalties at the appropriate rounds")
    add_bullet(doc, "Generate the SBRI Certificate at game end")

    add_bold_body(doc,
        "Note: ",
        "BRSR mode can be run alongside standard-mode teams in the same class. "
        "Each team's paradigm is set independently at session creation time.")

    # ── Common Misconceptions ──
    add_heading(doc, "Common Student Misconceptions to Address", level=2)

    add_bullet(doc,
        "\"Status Quo is free, so it's always better.\" — Correct this by pointing to the "
        "CPCB (₹50 Lakh) and SEBI (₹1 Crore) penalties. The 'free' option often costs more "
        "than the Leadership option over the full 10-round horizon.")
    add_bullet(doc,
        "\"Only Round 5 matters for the grade.\" — Clarify that each round updates a different "
        "dimension. Scoring 80 in Reporting Quality (R5) but 5 in Governance Ethics (R1) "
        "produces a blended score of ~40 — a 'D' grade.")
    add_bullet(doc,
        "\"We can recover from Governance Fragility.\" — The governance fragility flag is "
        "a ratchet: once set in R1, governance risk score compounds every subsequent round. "
        "By R5, the Whistleblower Crisis adds +15 to governance risk. There is no 'undo'.")
    add_bullet(doc,
        "\"The Green Bond discount is automatic.\" — Two conditions must be met: the team "
        "must file an Integrated Report in R5 AND have a BRSR score ≥ 70. Missing either "
        "condition means no NCD interest rate discount.")


# ═════════════════════════════════════════════════════════════════
#  RUNNER
# ═════════════════════════════════════════════════════════════════
def process(filepath, add_fn, label, output_suffix="_v7"):
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return

    doc = docx.Document(filepath)
    add_fn(doc)

    base, ext = os.path.splitext(os.path.basename(filepath))
    # Remove existing version suffix and add new one
    # e.g. "Muressons_Student_Manual_v6" -> "Muressons_Student_Manual_v7"
    if base.endswith("_v6"):
        base = base[:-3]
    out_name = f"{base}_v7{ext}"
    out_path = os.path.join(BASE_DIR, out_name)
    doc.save(out_path)
    print(f"[OK] {label} saved -> {out_name}")
    return out_path


if __name__ == '__main__':
    process(STUDENT_MANUAL, add_player_section, "Player Manual")
    process(FACILITATOR_MANUAL, add_facilitator_section, "Facilitator Manual")
