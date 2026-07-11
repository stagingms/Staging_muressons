"""
Append comprehensive BRSR NGRBC sections to both manuals.
Produces:
  - Muressons_Facilitator_Manual_v10.docx
  - Muressons_Student_Manual_v9.docx
"""

import copy
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

# ─────────────────────────────────────────────────────────────────
#  UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────

def add_styled_heading(doc, text, level):
    """Add a heading, reusing the document's existing style."""
    h = doc.add_heading(text, level=level)
    return h


def add_body(doc, text, bold=False, italic=False):
    """Add a body paragraph."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    return p


def add_table(doc, headers, rows, shade_header=True):
    """Add a formatted table."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(9)
        if shade_header:
            shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="1F3864"/>')
            cell._tc.get_or_add_tcPr().append(shading)
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.color.rgb = RGBColor(255, 255, 255)

    # Data rows
    for r_idx, row_data in enumerate(rows):
        row = table.rows[1 + r_idx]
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.text = str(val)
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)

    doc.add_paragraph()  # spacing
    return table


def add_bullet(doc, text, bold_prefix=None):
    """Add a bullet point, optionally with a bold prefix."""
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        run = p.add_run(bold_prefix)
        run.bold = True
        p.add_run(text)
    else:
        p.add_run(text)
    return p


def add_note_box(doc, text, label="NOTE"):
    """Add a styled note/warning paragraph."""
    p = doc.add_paragraph()
    run = p.add_run(f"[{label}] ")
    run.bold = True
    run.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    p.add_run(text)
    return p


# ─────────────────────────────────────────────────────────────────
#  SECTION BUILDER: FACILITATOR MANUAL
# ─────────────────────────────────────────────────────────────────

def build_facilitator_brsr_section(doc):
    """Append the comprehensive BRSR section to the facilitator manual."""

    doc.add_page_break()
    add_styled_heading(doc, "Section: BRSR NGRBC Decision Paradigm — Complete Facilitator Guide", 1)

    # ── Overview ──
    add_styled_heading(doc, "Overview", 2)
    add_body(doc, (
        "The BRSR (Business Responsibility and Sustainability Reporting) NGRBC "
        "(National Guidelines on Responsible Business Conduct) pathway is a 10-round "
        "decision paradigm aligned with India-specific ESG regulatory challenges. "
        "It is designed for courses focused on Indian corporate governance, "
        "SEBI regulations, and the NGRBC framework."
    ))
    add_body(doc, (
        "When the BRSR paradigm is selected by the facilitator, the simulation runs for "
        "10 rounds, and the display currency defaults to Indian Rupees (₹). "
        "Each round maps to specific NGRBC Principles (P1–P9), with escalating regulatory "
        "pressure culminating in a terminal BRSR filing."
    ))

    add_note_box(doc, (
        "The BRSR paradigm is a STANDALONE paradigm — it replaces the standard Legacy A/B/C "
        "and Strategic Pillars modes entirely. It cannot be combined with the SDG or Healthcare paradigms."
    ), "IMPORTANT")

    # ── How to Activate ──
    add_styled_heading(doc, "How to Activate", 2)
    add_bullet(doc, "Open the Facilitator Dashboard → Cohort Settings → Decision Paradigm")
    add_bullet(doc, 'Select "BRSR NGRBC Edition" (🇮🇳 icon)')
    add_bullet(doc, "The paradigm is locked after selection — it cannot be changed mid-game")
    add_bullet(doc, "All player sessions in the cohort will inherit the BRSR paradigm")

    # ── Dual Decision Interface ──
    add_styled_heading(doc, "Dual Decision Interface", 2)
    add_body(doc, (
        "The BRSR paradigm supports two parallel decision modes. Players see both simultaneously:"
    ))
    add_body(doc, "1. Legacy A/B/C Options — Three strategic options per round graded by ambition:", bold=True)
    add_table(doc,
        ["Grade", "Pattern", "Description"],
        [
            ["Option A", "Leadership Indicator", "Maximum investment, exceeds SEBI requirements, sets governance best-practice flags"],
            ["Option B", "Essential Indicators", "Moderate investment, meets all Essential Indicator requirements"],
            ["Option C", "Below Compliance", "Minimal/zero investment, fails Leadership requirements, sets risk flags"],
        ])

    add_body(doc, "2. Strategic Pillars Mode — Five independent pillar areas per round, each with 3 granular options:", bold=True)
    add_table(doc,
        ["Area Key", "Typical Labels (vary by round)"],
        [
            ["energy", "Board ESG Governance / Water & Discharge / Supply Chain Traceability / Integrated Reporting"],
            ["operations", "Ethics & Anti-Corruption / OHS Compliance / EPR & Waste / Assurance & Verification"],
            ["supply_chain", "Stakeholder Engagement / Human Rights DD / Circular Economy / Disclosure Cross-Refs"],
            ["offsetting", "CSR Impact Reporting / Wage & Welfare Fund / Climate Disclosure / Materiality Validation"],
            ["human_resources", "Board Diversity / DEI & Pay Equity / Green Skills / Investor Communication"],
        ])

    add_body(doc, (
        "When players use Strategic Pillars mode, their selections are automatically translated "
        "to the closest legacy option_a/b/c using a flag-based priority system with cost-based fallback."
    ))

    # ── NGRBC Principle Mapping ──
    add_styled_heading(doc, "NGRBC Principle Mapping", 2)
    add_table(doc,
        ["Round", "NGRBC Principles", "Theme"],
        [
            ["R1", "P1 (Ethics & Transparency), P7 (Policy Advocacy)", "Governance structures, board declarations, political contributions"],
            ["R2", "P3 (Employee Wellbeing), P5 (Human Rights)", "Living wages, OHS, POSH, DEI, supply chain HRDD"],
            ["R3", "P6 (Environmental Protection), P2 (Sustainable Products)", "Water discharge, EPR, circularity, climate disclosure, Scope 3"],
            ["R4", "P4 (Stakeholder Engagement), P8 (Inclusive Growth)", "BRSR Core, value chain assurance, supplier development"],
            ["R5", "P9 (Customer Value), P1–P8 (Integrated)", "Final disclosure, ESG-financial connectivity, materiality validation"],
        ])

    # ── Round-by-Round Content ──
    add_styled_heading(doc, "Round-by-Round Facilitator Guide", 2)

    # Round 1
    add_styled_heading(doc, "Round 1 — Governance & Transparency (P1 & P7)", 3)
    add_body(doc, (
        "Crisis: SEBI notifies the top 1,000 listed companies. Muressons must establish "
        "a BRSR Steering Committee. MCA's NGRBC guidelines require a signed Board declaration. "
        "Political contributions from the Consumer Goods BU's lobbying in Delhi surface in an RTI query."
    ), italic=True)

    add_body(doc, "Legacy Options:", bold=True)
    add_table(doc,
        ["Option", "Title", "Treasury", "Reputation", "Gov. Risk", "Key Flags"],
        [
            ["A", "Radical Transparency (Leadership)", "−₹4.0M", "+10", "−8", "brsr_pioneer, brsr_indicator_leadership"],
            ["B", "Standard Compliance (Essential)", "−₹2.0M", "+5", "−3", "brsr_indicator_essential"],
            ["C", "Reactive Disclosure (Below)", "−₹0.5M", "−5", "+10", "governance_fragility"],
        ])

    add_body(doc, "Strategic Pillars:", bold=True)
    add_table(doc,
        ["Area", "Leadership Option (Cost)", "Essential Option (Cost)", "Status Quo"],
        [
            ["⚡ Board ESG Governance", "Board ESG Committee (−₹3M)", "Compliance Sub-Committee (−₹1M)", "No Action"],
            ["🏭 Ethics & Anti-Corruption", "Ethics Officer + Whistleblower (−₹2M)", "Basic Code of Conduct (−₹800K)", "No Action"],
            ["🔗 Stakeholder Engagement", "Multi-Stakeholder Advisory (−₹2.5M)", "Annual Stakeholder Meet (−₹800K)", "No Action"],
            ["🌱 CSR Impact Reporting", "CSR Impact Dashboard (−₹1.5M)", "Basic CSR Report (−₹500K)", "No Investment"],
            ["👥 Board Diversity", "Board Diversity Matrix (−₹1.2M)", "Gender Disclosure (−₹400K)", "No HR Action"],
        ])

    add_body(doc, "Hidden Mechanics (DO NOT REVEAL):", bold=True)
    add_bullet(doc, "Option C sets governance_fragility — this cascades forward with compounding 4% governance drag from R3, and triggers a Whistleblower Leak crisis at R5 (−₹2.5M treasury)")
    add_bullet(doc, "Option A sets brsr_pioneer — contributes to BRSR Pioneer archetype and ESG Alpha Dividend")

    add_body(doc, "Debrief Prompts:", bold=True)
    add_bullet(doc, "How does SEBI's 'comply or explain' approach differ from the EU's CSRD mandatory disclosure?")
    add_bullet(doc, "What are the trade-offs between a Board-level ESG Committee vs. embedding ESG in existing committees?")

    # Round 2
    add_styled_heading(doc, "Round 2 — Workforce & Human Rights (P3 & P5)", 3)
    add_body(doc, (
        "Crisis: Electronics BU unions in Chennai demand living wage disclosures (Leadership Indicator "
        "under P3). Pharma BU contract workers face OHS gaps at API plants. POSH committee reports "
        "highlight inconsistencies."
    ), italic=True)

    add_body(doc, "Legacy Options:", bold=True)
    add_table(doc,
        ["Option", "Title", "Treasury", "Social License", "Burnout", "Flags"],
        [
            ["A", "Living Wage Standard (Leadership)", "−₹8.0M", "+15", "−12", "brsr_living_wage"],
            ["B", "Safety & POSH Focus (Essential+)", "−₹4.0M", "+5", "−5", "brsr_indicator_essential"],
            ["C", "Statutory Minimums Only", "₹0", "−10", "+5", "brsr_statutory_minimums"],
        ])

    add_body(doc, "Strategic Pillars:", bold=True)
    add_table(doc,
        ["Area", "Leadership Option (Cost)", "Essential Option (Cost)", "Status Quo"],
        [
            ["⚡ OHS Compliance", "ISO 45001 Upgrade (−₹3M)", "Basic Safety Audit (−₹1M)", "No Action"],
            ["🏭 Labour Practices", "Fair Wage Transparency (−₹2.5M)", "Wage Disclosure (−₹800K)", "No Action"],
            ["🔗 Human Rights DD", "Tier-1 HRDD (−₹2.5M)", "Supplier Questionnaire (−₹500K)", "Defer"],
            ["🌱 Wage & Welfare Fund", "Living Wage Gap Fund (−₹2M)", "Statutory Compliance Fund (−₹600K)", "No Investment"],
            ["👥 DEI & Pay Equity", "DEI Dashboard & Training (−₹1.5M)", "Gender Pay Audit (−₹700K)", "No HR Action"],
        ])

    add_body(doc, "Hidden Mechanics:", bold=True)
    add_bullet(doc, "Option A reduces burnout by 12 across ALL BUs and increases workforce readiness by 8")
    add_bullet(doc, "Option C increases strike probability by +0.15 (capped at 0.6) and sets brsr_labor_unrest_risk")
    add_body(doc, "Theory Connection:", bold=True)
    add_bullet(doc, "NGRBC Principle 3 — living wage as a Leadership Indicator, not just minimum wage compliance")
    add_bullet(doc, "UN Guiding Principles on Business and Human Rights (UNGPs) — HRDD methodology")

    # Round 3
    add_styled_heading(doc, "Round 3 — Environment & Circularity (P6 & P2)", 3)
    add_body(doc, (
        "Crisis: CPCB flags Pharma BU's water discharge for API residues. EPR scrutiny for Electronics "
        "(e-waste) and Consumer Goods (plastics). BRSR demands Scope 1+2 GHG intensity."
    ), italic=True)

    add_body(doc, "Legacy Options:", bold=True)
    add_table(doc,
        ["Option", "Title", "Treasury", "NCD", "Carbon", "Flags"],
        [
            ["A", "Circular Symbiosis & ZLD (Leadership)", "−₹10.0M", "−15", "−5", "brsr_circular_symbiosis"],
            ["B", "Efficiency Upgrades & EPR (Essential+)", "−₹6.0M", "−8", "—", "brsr_indicator_essential"],
            ["C", "Regulatory Minimums", "−₹2.0M", "+5", "+2", "brsr_regulatory_minimum"],
        ])

    add_body(doc, "Strategic Pillars:", bold=True)
    add_table(doc,
        ["Area", "Leadership Option (Cost)", "Essential Option (Cost)", "Status Quo"],
        [
            ["⚡ Water & Discharge", "ZLD for Pharma API (−₹3M)", "Water Recycling (−₹1.2M)", "No Change"],
            ["🏭 EPR & Waste Mgmt", "EPR Full Compliance (−₹2.5M)", "Basic Segregation (−₹800K)", "No Change"],
            ["🔗 Circular Economy", "Waste-to-Energy Partner (−₹1.8M)", "EPR Registration (−₹600K)", "Defer"],
            ["🌱 Climate Disclosure", "SBTi Scope 3 Pathway (−₹2.5M)", "Scope 1+2 Reporting (−₹800K)", "No Investment"],
            ["👥 Green Skills", "Green Skills Academy (−₹1.5M)", "Basic EHS Training (−₹400K)", "No HR Action"],
        ])

    add_body(doc, "Hidden Mechanics:", bold=True)
    add_bullet(doc, "Option A: NCD interest rate reduced by 1.2%, synergy multiplier +0.30 (capped at 1.5)")
    add_bullet(doc, "Option C: CPCB penalty of −₹5M treasury, NCD rate +1%")
    add_bullet(doc, "If governance_fragility is active from R1, a compounding 4% governance drag activates this round")

    # Round 4
    add_styled_heading(doc, "Round 4 — Value Chain & BRSR Core", 3)
    add_body(doc, (
        "Crisis: SEBI introduces 'BRSR Core' for value chain disclosures. Muressons falls in "
        "the top 250 glide path — reasonable assurance mandatory for 9 key attributes. Tier-2 "
        "electronics suppliers face child labor scrutiny."
    ), italic=True)

    add_body(doc, "Legacy Options:", bold=True)
    add_table(doc,
        ["Option", "Title", "Treasury", "Reputation", "Gov. Risk", "Flags"],
        [
            ["A", "Multi-Tier Assurance (Leadership)", "−₹6.0M", "+12", "−10", "brsr_core_assured"],
            ["B", "Tier-1 Screening (Essential)", "−₹2.0M", "+4", "−3", "brsr_indicator_essential"],
            ["C", "Self-Assessment Only", "−₹0.5M", "−8", "+8", "brsr_greenwash_risk"],
        ])

    add_body(doc, "Strategic Pillars:", bold=True)
    add_table(doc,
        ["Area", "Leadership Option (Cost)", "Essential Option (Cost)", "Status Quo"],
        [
            ["⚡ Supply Chain Traceability", "Blockchain Traceability (−₹3M)", "Tier-1 Digital Portal (−₹1M)", "No Change"],
            ["🏭 Assurance & Verification", "Big 4 Reasonable Assurance (−₹2.5M)", "Limited Assurance (−₹1.2M)", "Self-Assessment (−₹300K)"],
            ["🔗 Supplier Development", "MSME Supplier Dev (−₹2M)", "Annual Supplier Audit (−₹800K)", "Defer"],
            ["🌱 Consumer & Stakeholder", "Consumer Grievance Analytics (−₹1.8M)", "CSR Documentation (−₹500K)", "No Investment"],
            ["👥 Supplier ESG Capacity", "ESG Training Program (−₹1.5M)", "Basic Awareness (−₹400K)", "No HR Action"],
        ])

    add_body(doc, "Hidden Mechanics:", bold=True)
    add_bullet(doc, "CRITICAL: Option C sets brsr_greenwash_risk — triggers a SEBI Show-Cause Notice with −12 reputation and −₹10M SEBI penalty. Audit tolerance drops to 20 (hostile).")
    add_bullet(doc, "Option A: reputation +8, audit tolerance ≥65 (protected). In R5, crisis severity is reduced by 10.")

    # Round 5
    add_styled_heading(doc, "Round 5 — Integrated Disclosure & ESG Alpha", 3)
    add_body(doc, (
        "Crisis: FY-end filing deadline. The Board demands the final BRSR submission. "
        "Investor Relations must present the ESG narrative to CRISIL and Sustainalytics."
    ), italic=True)

    add_body(doc, "Legacy Options:", bold=True)
    add_table(doc,
        ["Option", "Title", "Treasury", "Reputation", "Flags"],
        [
            ["A", "Integrated Report (Leadership)", "−₹4.0M", "+15", "brsr_integrated_report"],
            ["B", "Strategic BRSR (Essential+)", "−₹2.0M", "+6", "brsr_indicator_essential"],
            ["C", "Compliance File", "−₹0.5M", "−3", "brsr_compliance_only"],
        ])

    add_body(doc, "Strategic Pillars:", bold=True)
    add_table(doc,
        ["Area", "Leadership Option (Cost)", "Essential Option (Cost)", "Status Quo"],
        [
            ["⚡ Integrated Reporting", "Six Capitals Report (−₹2.5M)", "Strategic KPIs (−₹1M)", "Minimal Filing (−₹200K)"],
            ["🏭 ESG-Financial Connectivity", "ESG-Financial Dashboard (−₹2M)", "Sector Benchmarking (−₹800K)", "No Change"],
            ["🔗 Disclosure Cross-Refs", "GRI/TCFD Mapping (−₹1.5M)", "Basic GRI Index (−₹500K)", "Defer"],
            ["🌱 Materiality Validation", "Third-Party Materiality (−₹2M)", "Internal Matrix (−₹600K)", "No Investment"],
            ["👥 Investor Communication", "Analyst & IR ESG Pack (−₹1.2M)", "Board Summary (−₹400K)", "No HR Action"],
        ])

    add_body(doc, "Hidden Mechanics:", bold=True)
    add_bullet(doc, "Option A: ESG Alpha Dividend = +0.05 M_R (5% terminal valuation uplift). If score ≥70, CRISIL AAA Green Bond discount: NCD rate −1.5%")
    add_bullet(doc, "Option C: Blocks Truth Premium, NCD rate +1.5% (green bond downgrade)")
    add_bullet(doc, "If governance_fragility active: Whistleblower Leak crisis fires — treasury −₹2.5M, governance risk +15")

    # ── Scoring Mechanics ──
    add_styled_heading(doc, "Scoring Mechanics", 2)

    add_styled_heading(doc, "BRSR Performance Score (0–100)", 3)
    add_body(doc, "The BRSR Score is computed across 5 weighted dimensions mapped to NGRBC principles:")
    add_table(doc,
        ["Dimension", "Weight", "Principles", "Score Derivation"],
        [
            ["Governance & Ethics", "20%", "P1, P7", "brsr_pioneer → 100 · governance_fragility → 20 · else 60"],
            ["Human Capital", "20%", "P3, P5", "brsr_living_wage → 100 · else 50"],
            ["Environmental Stewardship", "25%", "P6, P2", "brsr_circular_symbiosis → 100 · sdg_12_leadership → 80 · else 40"],
            ["Value Chain & Stakeholder", "20%", "P4, P8, P9", "brsr_core_assured → 100 · brsr_greenwash_risk → 20 · else 50"],
            ["Integrated Disclosure", "15%", "All", "brsr_integrated_report → 100 · else 40"],
        ])

    add_body(doc, "Formula: BRSR Score = Σ(dimension_score × weight)", bold=True)

    add_styled_heading(doc, "Grading & Archetypes", 3)
    add_table(doc,
        ["Grade", "Score Range", "Archetype", "Description"],
        [
            ["A+", "≥ 90", "BRSR Pioneer 🏆", "Exemplary NGRBC Leadership + rigorous assurance"],
            ["A", "80–89", "Responsible Steward 🌿", "Meets Essential reliably, strategic Leadership in material areas"],
            ["B", "60–79", "Compliance Pragmatist 📋", "Mandatory compliance but unchecked ESG risks"],
            ["C", "40–59", "Compliance Pragmatist 📋", "Minimum viable compliance"],
            ["D", "20–39", "Regulatory Laggard ⚠️", "Fails basic Essential indicators"],
            ["F", "< 20", "Regulatory Laggard ⚠️", "Complete failure, high regulatory risk"],
        ])

    add_styled_heading(doc, "Terminal Valuation Impact", 3)
    add_table(doc,
        ["Condition", "M_R Impact"],
        [
            ["BRSR Pioneer (all A choices, score ≥ 90)", "+0.05 M_R (ESG Alpha Dividend)"],
            ["brsr_integrated_report active", "No disclosure haircut (full exit multiple)"],
            ["brsr_compliance_only at R5", "Disclosure haircut applied"],
            ["brsr_greenwash_risk active", "ESG risk discount on valuation"],
        ])

    add_note_box(doc, (
        "Maximum M_R achievable with a full BRSR Pioneer path is approximately ~1.98 "
        "(1.0 base + 0.05 BRSR + wellbeing/steward bonuses − instability adjustments)."
    ), "TIP")

    # ── Crisis Events ──
    add_styled_heading(doc, "BRSR-Specific Crisis Events", 3)
    add_table(doc,
        ["Event", "Trigger", "Impact"],
        [
            ["SEBI Show-Cause Notice", "brsr_greenwash_risk at R4", "−12 reputation, −₹10M SEBI penalty"],
            ["Whistleblower Governance Leak", "governance_fragility at R5", "−₹2.5M treasury, gov risk +15"],
            ["Assurance Bonus", "brsr_core_assured at R5", "Crisis severity −10"],
        ])

    # ── Flag Cascade System ──
    add_styled_heading(doc, "Flag Cascade System", 2)
    add_body(doc, (
        "Flags set in earlier rounds cascade forward to influence later round outcomes and "
        "final scoring. This is the core pedagogical mechanism — early decisions have compounding effects."
    ))
    add_table(doc,
        ["Flag", "Set By", "Cascade Effect"],
        [
            ["brsr_pioneer", "R1 Option A", "Gov risk −8 all BUs. Contributes to Pioneer archetype."],
            ["governance_fragility", "R1 Option C", "R3: +4% gov drag. R5: crisis+15, whistleblower −₹2.5M."],
            ["brsr_living_wage", "R2 Option A", "Burnout −12 all BUs. Workforce readiness +8."],
            ["brsr_statutory_minimums", "R2 Option C", "Strike risk +0.15 (capped 0.6). Labour unrest flag."],
            ["brsr_circular_symbiosis", "R3 Option A", "NCD rate −1.2%. Synergy +0.30."],
            ["brsr_regulatory_minimum", "R3 Option C", "NCD rate +1%. CPCB penalty −₹5M."],
            ["brsr_core_assured", "R4 Option A", "Rep +8. Audit tolerance ≥65. R5: crisis −10."],
            ["brsr_greenwash_risk", "R4 Option C", "Audit →20 (hostile). SEBI −₹10M. Rep −12."],
            ["brsr_integrated_report", "R5 Option A", "+0.05 M_R. NCD −1.5% if score ≥70."],
            ["brsr_compliance_only", "R5 Option C", "Truth Premium blocked. NCD +1.5%."],
        ])

    # ── Pillar → Legacy Translation ──
    add_styled_heading(doc, "Pillar → Legacy Translation Rules", 2)
    add_table(doc,
        ["Round", "option_a Flag Trigger", "option_b Flag Trigger", "option_c Flag Trigger"],
        [
            ["1", "brsr_pioneer", "brsr_ethics_officer", "governance_fragility"],
            ["2", "brsr_living_wage", "brsr_indicator_essential", "brsr_statutory_minimums"],
            ["3", "brsr_circular_symbiosis", "brsr_indicator_essential", "brsr_regulatory_minimum"],
            ["4", "brsr_core_assured", "brsr_indicator_essential", "brsr_greenwash_risk"],
            ["5", "brsr_integrated_report", "brsr_indicator_essential", "brsr_compliance_only"],
        ])
    add_body(doc, (
        "Cost-based fallback: If no flag matches, total pillar cost ≤ −₹8M → option_a, "
        "≤ −₹3M → option_b, else → option_c."
    ))

    # ── BRSR Certificate ──
    add_styled_heading(doc, "BRSR Certificate (Game Over)", 2)
    add_body(doc, (
        "When the BRSR track completes at Round 10, the Game Over screen renders a BRSR NGRBC "
        "Certificate showing the player's grade, archetype, compliance score out of 100, and a "
        "5-column NGRBC Principle pass/fail grid. Each principle is marked ✅ if the player chose "
        "at least Essential-level compliance (not option_c)."
    ))

    # ── Facilitator Talking Points ──
    add_styled_heading(doc, "Facilitator Talking Points", 2)

    add_body(doc, "Post-Round 1:", bold=True)
    add_bullet(doc, "How does SEBI's 'comply or explain' differ from the EU's CSRD mandatory disclosure?")
    add_bullet(doc, "What governance structures does the NGRBC framework recommend beyond a compliance committee?")

    add_body(doc, "Post-Round 2:", bold=True)
    add_bullet(doc, "Why is living wage a Leadership Indicator and not an Essential one under P3?")
    add_bullet(doc, "How do POSH compliance gaps affect organisational social license?")

    add_body(doc, "Post-Round 3:", bold=True)
    add_bullet(doc, "What is the business case for Zero Liquid Discharge vs. the cost of regulatory penalties?")
    add_bullet(doc, "How does EPR compliance create circular revenue streams?")

    add_body(doc, "Post-Round 4:", bold=True)
    add_bullet(doc, "What is the difference between limited and reasonable assurance? Why does BRSR Core mandate the latter?")
    add_bullet(doc, "How does greenwash risk compound with earlier governance choices?")

    add_body(doc, "Post-Round 5 (Debrief):", bold=True)
    add_bullet(doc, "Compare your BRSR score with peers — what decisions drove the biggest divergence?")
    add_bullet(doc, "How does the ESG Alpha Dividend concept translate to real-world ESG-linked valuations?")
    add_bullet(doc, "Discuss the 'compounding cost of inaction' — how did R1 governance choices affect R5 outcomes?")

    # ── God Mode Controls ──
    add_styled_heading(doc, "God Mode Controls", 2)
    add_body(doc, (
        "The God Mode Intelligence Panel includes a BRSR section showing platform-wide data: "
        "Track Completions, BRSR Pioneers, Greenwash Risk count, Governance Fragility count, "
        "Average BRSR Score, and Crises Injected. The engine toggle 'brsr_ngrbc_enabled' can "
        "enable/disable the BRSR track dynamically."
    ))


# ─────────────────────────────────────────────────────────────────
#  SECTION BUILDER: STUDENT/PLAYER MANUAL
# ─────────────────────────────────────────────────────────────────

def build_student_brsr_section(doc):
    """Append the comprehensive BRSR section to the student manual."""

    doc.add_page_break()
    add_styled_heading(doc, "Section: BRSR NGRBC Decision Paradigm — Player Guide", 1)

    # ── Overview ──
    add_styled_heading(doc, "What is the BRSR NGRBC Paradigm?", 2)
    add_body(doc, (
        "The BRSR (Business Responsibility and Sustainability Reporting) NGRBC "
        "(National Guidelines on Responsible Business Conduct) paradigm is an alternative "
        "10-round simulation track that immerses you in India's ESG regulatory environment. "
        "You face 10 rounds of India-specific challenges aligned to SEBI's BRSR framework."
    ))
    add_body(doc, (
        "You will navigate SEBI mandates, CPCB environmental compliance, labour reforms, "
        "supply chain due diligence, and the final BRSR filing — with every decision "
        "carrying long-term consequences for your terminal valuation."
    ))

    add_note_box(doc, (
        "When the BRSR paradigm is active, the simulation runs for 10 rounds "
        "and displays currency in Indian Rupees (₹)."
    ))

    # ── How It Works ──
    add_styled_heading(doc, "How It Works", 2)
    add_body(doc, "Each round, you make decisions across 5 Strategic Pillar areas:")
    add_table(doc,
        ["Pillar", "What It Covers"],
        [
            ["⚡ Energy / Governance", "Board committees, water systems, supply chain traceability, reporting"],
            ["🏭 Operations", "Ethics, OHS, waste management, assurance, ESG connectivity"],
            ["🔗 Supply Chain", "Stakeholder engagement, HRDD, circular economy, cross-references"],
            ["🌱 Offsetting / Investment", "CSR, welfare funds, climate disclosure, materiality validation"],
            ["👥 Human Resources", "Board diversity, DEI, green skills, investor communication"],
        ])

    add_body(doc, (
        "For each pillar, you choose one of three options ranging from Leadership (highest cost, "
        "highest impact) to Status Quo (zero cost, negative consequences). Your choices set flags "
        "that cascade through future rounds."
    ))

    # ── Round Walkthrough ──
    add_styled_heading(doc, "Round-by-Round Walkthrough", 2)

    # R1
    add_styled_heading(doc, "Round 1: Governance & Transparency (P1 & P7)", 3)
    add_body(doc, (
        "SEBI has mandated BRSR reporting for the top 1,000 listed companies. As Muressons' "
        "sustainability head, you must decide: do you establish a Board-level ESG Committee, "
        "appoint an independent ethics officer, and publish a transparency register? Or do you "
        "rely on the existing compliance team and file the bare minimum?"
    ))
    add_body(doc, "Key Trade-off:", bold=True)
    add_bullet(doc, "Leadership investment (−₹4M) sets you up as a BRSR Pioneer with long-term governance benefits")
    add_bullet(doc, "Reactive disclosure (−₹0.5M) saves cash now but sets a governance_fragility flag that will haunt you in later rounds")

    add_note_box(doc, (
        "Your governance choice in Round 1 compounds through the entire simulation. "
        "Poor governance in R1 triggers a Whistleblower Leak at R5!"
    ), "WARNING")

    # R2
    add_styled_heading(doc, "Round 2: Workforce & Human Rights (P3 & P5)", 3)
    add_body(doc, (
        "Unions at the Chennai Electronics plant demand living wage disclosures. The Pharma BU "
        "faces OHS gaps at API plants. POSH committee reports highlight inconsistencies. How much "
        "will you invest in your workforce?"
    ))
    add_body(doc, "Key Trade-off:", bold=True)
    add_bullet(doc, "Living Wage Standard (−₹8M) reduces burnout across all BUs by 12 points")
    add_bullet(doc, "Statutory Minimums (₹0) increases strike probability and risks labour unrest")

    # R3
    add_styled_heading(doc, "Round 3: Environment & Circularity (P6 & P2)", 3)
    add_body(doc, (
        "CPCB flags your Pharma BU's water discharge. Electronics and Consumer Goods face EPR "
        "scrutiny. This round tests your environmental stewardship — from Zero Liquid Discharge "
        "to Scope 3 climate pathways."
    ))
    add_body(doc, "Key Trade-off:", bold=True)
    add_bullet(doc, "Circular Symbiosis (−₹10M) reduces your natural capital debt rate and boosts synergy")
    add_bullet(doc, "Regulatory Minimums (−₹2M) leads to CPCB penalties and rising debt costs")

    # R4
    add_styled_heading(doc, "Round 4: Value Chain & BRSR Core", 3)
    add_body(doc, (
        "SEBI introduces 'BRSR Core' — reasonable assurance is now mandatory for the top 250 "
        "companies. Your supply chain faces scrutiny. Do you invest in blockchain traceability "
        "and Big 4 assurance, or rely on self-assessment?"
    ))

    add_note_box(doc, (
        "Self-Assessment (Option C) triggers a SEBI Show-Cause Notice with −12 reputation "
        "and −₹10M penalty. This is the most consequential single decision in the BRSR track!"
    ), "WARNING")

    # R5
    add_styled_heading(doc, "Round 5: Integrated Disclosure & ESG Alpha", 3)
    add_body(doc, (
        "The final BRSR filing. CRISIL ESG and Sustainalytics are benchmarking you against peers. "
        "Your choice: publish a Six Capitals integrated report with GRI/TCFD cross-references, "
        "or file the bare minimum compliance document?"
    ))
    add_body(doc, "Key Trade-off:", bold=True)
    add_bullet(doc, "Integrated Report (−₹4M) unlocks the ESG Alpha Dividend — a +5% boost to your terminal valuation multiplier")
    add_bullet(doc, "Compliance File (−₹0.5M) blocks the Truth Premium and downgrades your green bond rating")

    # ── Understanding Your BRSR Score ──
    add_styled_heading(doc, "Understanding Your BRSR Score", 2)
    add_body(doc, "Your BRSR Score (0–100) is calculated from 5 dimensions:")
    add_table(doc,
        ["Dimension", "Weight", "What Drives It"],
        [
            ["Governance & Ethics", "20%", "Your R1 governance investment level"],
            ["Human Capital", "20%", "Your R2 workforce & human rights choices"],
            ["Environmental Stewardship", "25%", "Your R3 environment & circularity decisions"],
            ["Value Chain & Stakeholder", "20%", "Your R4 assurance & supply chain choices"],
            ["Integrated Disclosure", "15%", "Your R5 final reporting quality"],
        ])

    add_styled_heading(doc, "What Your Grade Means", 3)
    add_table(doc,
        ["Grade", "Score", "Archetype", "What It Means"],
        [
            ["A+", "≥ 90", "BRSR Pioneer 🏆", "Exemplary — you exceeded all Leadership Indicators"],
            ["A", "80–89", "Responsible Steward 🌿", "Strong — Essential compliance with strategic Leadership"],
            ["B", "60–79", "Compliance Pragmatist 📋", "Adequate — met SEBI minimums but left ESG value on table"],
            ["C–F", "< 60", "Regulatory Laggard ⚠️", "Risk — failed Essential indicators, regulatory exposure"],
        ])

    # ── The Cascade Effect ──
    add_styled_heading(doc, "The Cascade Effect — Why Early Decisions Matter", 2)
    add_body(doc, (
        "The BRSR paradigm is designed to teach systems thinking. Your decisions in early rounds "
        "compound and cascade through later rounds. Here are the key cascades to watch for:"
    ))
    add_bullet(doc, "R1 Governance →", bold_prefix="R1 → R5: ")
    add_bullet(doc, "Poor governance in R1 triggers a compounding 4% drag from R3 onward, and a Whistleblower Leak crisis at R5")
    add_bullet(doc, "R2 Workforce →", bold_prefix="R2 → R3: ")
    add_bullet(doc, "Labour unrest from R2 increases strike probability, affecting workforce transition in R3")
    add_bullet(doc, "R3 Environment →", bold_prefix="R3 → R5: ")
    add_bullet(doc, "Circular economy investments affect R5 integrated report credibility")
    add_bullet(doc, "R4 Assurance →", bold_prefix="R4 → R5: ")
    add_bullet(doc, "Greenwash risk from R4 blocks the Truth Premium at R5 and triggers SEBI penalties")

    # ── BRSR Certificate ──
    add_styled_heading(doc, "Your BRSR Certificate", 2)
    add_body(doc, (
        "At game end, you receive a BRSR NGRBC Certificate showing your grade, archetype, "
        "compliance score, and a principle-by-principle pass/fail grid across the 9 NGRBC Principles. "
        "Each principle is marked ✅ if you chose at least Essential-level compliance."
    ))

    # ── Strategic Tips ──
    add_styled_heading(doc, "Strategic Tips", 2)
    add_bullet(doc, "Don't skip governance in R1 — the governance_fragility flag compounds through all remaining rounds, costing far more than the ₹3.5M you save")
    add_bullet(doc, "R4 is the pivotal round — the Self-Assessment option looks cheap (₹500K) but triggers ₹10M+ in SEBI penalties plus reputation destruction")
    add_bullet(doc, "Budget for R5 — the Integrated Report costs ₹4M but unlocks a 5% terminal valuation bonus that typically exceeds ₹25M+ in value")
    add_bullet(doc, "Use the BRSR Dashboard (🇮🇳 icon in toolbar) to track your dimension scores in real-time")
    add_bullet(doc, "The Leadership/Essential/Status Quo framework mirrors real SEBI expectations — use this as a learning framework for actual BRSR compliance")

    # ── NGRBC Principles Reference ──
    add_styled_heading(doc, "NGRBC Principles Quick Reference", 2)
    add_table(doc,
        ["Principle", "Description", "Covered In"],
        [
            ["P1", "Businesses should conduct and govern themselves with integrity and ethics", "Round 1"],
            ["P2", "Businesses should provide goods and services in a sustainable manner", "Round 3"],
            ["P3", "Businesses should respect and promote the well-being of all employees", "Round 2"],
            ["P4", "Businesses should respect the interests of and be responsive to stakeholders", "Round 4"],
            ["P5", "Businesses should respect and promote human rights", "Round 2"],
            ["P6", "Businesses should respect and make efforts to protect the environment", "Round 3"],
            ["P7", "Businesses should engage responsibly with policy advocacy", "Round 1"],
            ["P8", "Businesses should promote inclusive growth and equitable development", "Round 4"],
            ["P9", "Businesses should engage with and provide value to customers responsibly", "Round 5"],
        ])

    # ── Theory Connections ──
    add_styled_heading(doc, "Theory Connections", 2)
    add_body(doc, "The BRSR paradigm connects to several academic frameworks:")
    add_bullet(doc, "Stakeholder Theory (Freeman, 1984) — the multi-stakeholder advisory in R1")
    add_bullet(doc, "UN Guiding Principles on Business & Human Rights (Ruggie, 2011) — HRDD methodology in R2")
    add_bullet(doc, "Circular Economy (Ellen MacArthur Foundation) — waste-to-energy partnerships in R3")
    add_bullet(doc, "Assurance Standards (ISAE 3000, ISAE 3410) — limited vs reasonable assurance in R4")
    add_bullet(doc, "Integrated Reporting (IIRC Six Capitals) — the final report framework in R5")
    add_bullet(doc, "Double Materiality (EFRAG/GRI) — materiality validation in R5")


# ─────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────

def main():
    import os
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ── Facilitator Manual ──
    fac_src = os.path.join(base, "Muressons_Facilitator_Manual_v9.docx")
    fac_dst = os.path.join(base, "Muressons_Facilitator_Manual_v10.docx")
    print(f"Loading {fac_src}...")
    fac_doc = Document(fac_src)
    build_facilitator_brsr_section(fac_doc)
    fac_doc.save(fac_dst)
    print(f"✅ Saved {fac_dst}")

    # ── Student Manual ──
    stu_src = os.path.join(base, "Muressons_Student_Manual_v8.docx")
    stu_dst = os.path.join(base, "Muressons_Student_Manual_v9.docx")
    print(f"Loading {stu_src}...")
    stu_doc = Document(stu_src)
    build_student_brsr_section(stu_doc)
    stu_doc.save(stu_dst)
    print(f"✅ Saved {stu_dst}")


if __name__ == "__main__":
    main()
