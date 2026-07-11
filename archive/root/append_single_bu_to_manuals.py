"""
append_single_bu_to_manuals.py
-------------------------------
Appends the Single-Business Mode & Regional Localisation sections
(with screenshots) to:
  - Muressons_Student_Manual_v6.docx       (Player Manual)
  - Muressons_Facilitator_Manual_v6.docx   (Facilitator Manual)

Outputs versioned copies:
  - Muressons_Student_Manual_v7.docx
  - Muressons_Facilitator_Manual_v7.docx

Run with:
    python append_single_bu_to_manuals.py
"""

import os
import docx
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE_DIR = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim"
IMG_DIR  = os.path.join(BASE_DIR, "guide_images")

STUDENT_IN     = os.path.join(BASE_DIR, "Muressons_Student_Manual_v6.docx")
FACILITATOR_IN = os.path.join(BASE_DIR, "Muressons_Facilitator_Manual_v6.docx")

STUDENT_OUT     = os.path.join(BASE_DIR, "Muressons_Student_Manual_v7.docx")
FACILITATOR_OUT = os.path.join(BASE_DIR, "Muressons_Facilitator_Manual_v7.docx")

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

def add_info_box(doc, text):
    """Add a shaded info-box paragraph."""
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'EEF2FF')   # light indigo tint
    pPr.append(shd)
    run = p.add_run(text)
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(55, 65, 81)
    return p


# ═════════════════════════════════════════════════════════════════
#  PLAYER SECTION  (Student Manual)
# ═════════════════════════════════════════════════════════════════

def add_player_section(doc):
    doc.add_page_break()

    # ── Title ──────────────────────────────────────────────────────
    add_heading(doc, "Section: Single Business Mode & Regional Localisation", level=1)

    add_body(doc,
        "Muressons now supports a Single Business Mode — a focused experience where your "
        "executive team manages one company operating in a specific geographic region, rather "
        "than a four-division conglomerate. In this mode, every strategic decision, stakeholder "
        "interaction, and sustainability challenge is shaped by both the industry vertical your "
        "facilitator has selected and the real-world regulatory and risk context of your region."
    )

    add_body(doc,
        "Whether you are managing an Agriculture company in South Asia, an Oil & Gas operation "
        "in Africa, a Retail FMCG brand across Europe, or a Technology firm in ASEAN, the "
        "simulation dynamically adjusts its pillar decisions, stakeholder profiles, black swan "
        "risks, and ESG reporting requirements to match your industry and region."
    )

    doc.add_paragraph()

    # ── What Is Single Business Mode ──────────────────────────────
    add_heading(doc, "What Is Single Business Mode?", level=2)

    add_body(doc,
        "In the standard simulation, you manage four business units simultaneously — Pharma, "
        "Electronics, Consumer Goods, and Software. In Single Business Mode, your cohort is "
        "assigned a single industry vertical and a geographic region. Your treasury, reputation, "
        "carbon position, and all five strategic pillars belong to that one business."
    )

    tbl = doc.add_table(rows=1, cols=3)
    tbl.style = 'Table Grid'
    add_table_header(tbl, "Feature", "Standard Mode (4-BU)", "Single Business Mode")
    add_table_row(tbl, "Companies managed", "4 Business Units", "1 Company")
    add_table_row(tbl, "Industry focus", "Generic conglomerate", "Specific vertical (e.g. Agriculture)")
    add_table_row(tbl, "Geographic context", "Global / generic", "Specific region (ASEAN, South Asia, Europe, North America, Africa)")
    add_table_row(tbl, "Stakeholder profiles", "Universal set", "Region & industry specific")
    add_table_row(tbl, "Strategic pillars", "5 standard areas", "5 areas — some replaced by industry-specific ones")
    add_table_row(tbl, "Black Swan events", "Global events only", "Region-filtered + new region-specific events")
    add_table_row(tbl, "ESG reporting", "Generic framework", "Region-aligned (BRSR, CSRD, SEC, ASEAN Taxonomy, King IV)")

    doc.add_paragraph()

    # ── The Five Regions ──────────────────────────────────────────
    add_heading(doc, "The Five Geographic Regions", level=2)

    add_body(doc,
        "Your facilitator selects the region when setting up your cohort. The region "
        "determines which stakeholders you must manage, which regulatory frameworks apply, "
        "and which black swan events you might face."
    )

    reg_tbl = doc.add_table(rows=1, cols=4)
    reg_tbl.style = 'Table Grid'
    add_table_header(reg_tbl, "Region", "Key Regulatory Framework", "Sample Stakeholders", "Region-Specific Risk")
    add_table_row(reg_tbl, "🌏 ASEAN",
        "ASEAN Taxonomy for Sustainable Finance",
        "MAS Regulator, FDI Investors, Supply Chain NGO",
        "🌀 Typhoon Supply Disruption")
    add_table_row(reg_tbl, "🇮🇳 South Asia",
        "SEBI BRSR / NGRBC Principles",
        "SEBI, Smallholder Farmers, AgriNGO, State Gov.",
        "🌡️ Monsoon Crisis / Heat Stress")
    add_table_row(reg_tbl, "🇪🇺 Europe",
        "CSRD / ESRS Directives",
        "EU Regulator, Consumer NGOs, ESG Bond Investors",
        "🌿 Carbon Border Adjustment Mechanism (CBAM)")
    add_table_row(reg_tbl, "🇺🇸 North America",
        "SEC Climate Disclosure Rules / TCFD",
        "SEC, Institutional Investors, Activist Shareholders",
        "📋 SEC Mandatory Climate Disclosure")
    add_table_row(reg_tbl, "🌍 Africa",
        "GRI Standards + King IV",
        "Host Government, Community Leaders, Resource Unions",
        "⛏️ Resource Nationalisation Risk")

    doc.add_paragraph()

    # ── Your Dashboard ────────────────────────────────────────────
    add_heading(doc, "Your Executive Cockpit in Single Business Mode", level=2)

    add_body(doc,
        "Your dashboard looks and works the same as the standard mode, but with two key differences: "
        "you see one company's financials (not four), and one or more of the five strategic pillar "
        "areas may be replaced by an industry-specific decision unique to your vertical."
    )

    add_image(doc, "single_bu_cockpit.png", width_inches=6.0,
              caption="Figure: Executive Cockpit in Single Business Mode (Agriculture, South Asia). "
                      "Note the 💧 Water Stewardship pillar replacing the standard Offsetting area.")

    add_info_box(doc,
        "ℹ️  The amber-highlighted pillar tile (💧 Water Stewardship in the example above) is "
        "your industry-specific pillar. It has been customised for your vertical by your institution "
        "and represents a material ESG issue specific to your industry."
    )

    doc.add_paragraph()

    # ── Industry-Specific Pillars ─────────────────────────────────
    add_heading(doc, "Industry-Specific Strategic Pillars", level=2)

    add_body(doc,
        "Depending on your assigned industry vertical, one or more of the five standard pillar "
        "areas may be replaced or extended with an industry-specific decision. These replacements "
        "reflect the material ESG issues that are most consequential for that sector."
    )

    pillar_tbl = doc.add_table(rows=1, cols=3)
    pillar_tbl.style = 'Table Grid'
    add_table_header(pillar_tbl, "Industry Vertical", "Replaced Pillar", "Industry-Specific Pillar")
    add_table_row(pillar_tbl, "🌾 Agriculture", "🌿 Offsetting", "💧 Water Stewardship")
    add_table_row(pillar_tbl, "🏦 Banking & Finance", "🔗 Supply Chain", "🤝 Financial Inclusion")
    add_table_row(pillar_tbl, "⛽ Oil & Gas", "🌿 Offsetting", "🛢️ Well Decommissioning")
    add_table_row(pillar_tbl, "💊 Pharma / Healthcare", "👥 Human Resources", "💊 Medicine Access")
    add_table_row(pillar_tbl, "💻 Technology", "🏭 Operations", "🔒 Data Privacy & Ethics")

    doc.add_paragraph()

    add_bold_body(doc,
        "Strategic Tip: ",
        "Your industry-specific pillar typically carries higher weight in your ESG score and "
        "is a key signal for regional regulators and stakeholders. Choosing the Status Quo "
        "option in your industry pillar carries a higher reputational risk than doing so in "
        "the standard pillar areas."
    )

    # ── Stakeholders ─────────────────────────────────────────────
    add_heading(doc, "Your Stakeholders — Industry & Region Specific", level=2)

    add_body(doc,
        "In Single Business Mode, your stakeholder landscape is drawn from a curated database "
        "specific to your industry and region combination. Each stakeholder has a power rating, "
        "interest level, and a Mendelow quadrant position reflecting real-world dynamics in your context."
    )

    add_image(doc, "single_bu_sentiment_panel.png", width_inches=5.5,
              caption="Figure: Stakeholder Sentiment Panel showing live attitude scores per stakeholder. "
                      "Green ▲ = improving, Red ▼ = deteriorating. Salience badges indicate priority.")

    add_body(doc,
        "Each round, the simulation tracks how your strategic decisions affect each stakeholder's "
        "attitude score (−100 Hostile → +100 Enthusiastic). The following factors drive sentiment changes:"
    )

    add_bullet(doc, "Your pillar decisions: choosing leadership options improves scores for aligned stakeholders")
    add_bullet(doc, "Black swan events: regional crises can sharply reduce community or regulator sentiment")
    add_bullet(doc, "Neglect: consistently choosing Status Quo erodes trust over multiple rounds")
    add_bullet(doc, "Salience matters: high-power 'Definitive' stakeholders amplify both gains and losses")

    add_info_box(doc,
        "⚠️  Watch for the 🚨 Early Warning badge on the Stakeholder Sentiment panel. "
        "This appears when a high-power stakeholder drops below −50 (Hostile territory). "
        "Hostile high-power stakeholders trigger reputational crises and regulatory interventions "
        "in subsequent rounds."
    )

    doc.add_paragraph()

    # ── Black Swans ───────────────────────────────────────────────
    add_heading(doc, "Region-Specific Black Swan Events", level=2)

    add_body(doc,
        "In addition to the global black swan events that can affect any simulation, Single Business "
        "Mode activates a set of region-specific disruptions. These events are based on real-world "
        "risk patterns in each geography."
    )

    bs_tbl = doc.add_table(rows=1, cols=3)
    bs_tbl.style = 'Table Grid'
    add_table_header(bs_tbl, "Event", "Region", "Impact")
    add_table_row(bs_tbl, "🚢 ASEAN Trade Dispute", "ASEAN",
        "Revenue −12%, Treasury −8%, logistics freeze")
    add_table_row(bs_tbl, "🌧️ South Asia Monsoon Crisis", "South Asia",
        "Factory closures, OPEX +10%, social licence at risk")
    add_table_row(bs_tbl, "🌿 Carbon Border Adjustment (CBAM)", "Europe",
        "Export revenue −8%, compliance cost spike")
    add_table_row(bs_tbl, "📋 SEC Climate Disclosure", "North America",
        "Legal fees, Governance risk +12, investor pressure")
    add_table_row(bs_tbl, "⛏️ Resource Nationalisation", "Africa",
        "Treasury −15%, Revenue −18%, community crisis")

    doc.add_paragraph()

    add_bold_body(doc,
        "Resilience Tip: ",
        "Black swan events are probabilistic — they are more likely to fire in later rounds "
        "(Rounds 4–8) and become more severe if your governance risk score is high or your "
        "community trust is low. Strong early investment in governance and community "
        "stakeholder engagement reduces both the probability and the impact of these events."
    )

    # ── ESG Reporting ────────────────────────────────────────────
    add_heading(doc, "ESG Reporting — Region-Aligned Frameworks", level=2)

    add_body(doc,
        "At the end of the simulation, your facilitator may generate a region-aligned ESG report "
        "summarising your performance across the frameworks most relevant to your geography. "
        "This is a teaching tool — it maps your decisions to the disclosure requirements you "
        "would face as a real company operating in your region."
    )

    esg_tbl = doc.add_table(rows=1, cols=2)
    esg_tbl.style = 'Table Grid'
    add_table_header(esg_tbl, "Region", "Primary Reporting Framework")
    add_table_row(esg_tbl, "🇮🇳 South Asia", "SEBI BRSR (Business Responsibility & Sustainability Reporting)")
    add_table_row(esg_tbl, "🇪🇺 Europe", "CSRD / European Sustainability Reporting Standards (ESRS)")
    add_table_row(esg_tbl, "🇺🇸 North America", "SEC Climate Rule / TCFD Aligned Disclosure")
    add_table_row(esg_tbl, "🌏 ASEAN", "ASEAN Taxonomy for Sustainable Finance")
    add_table_row(esg_tbl, "🌍 Africa", "GRI Standards + King IV Corporate Governance")

    doc.add_paragraph()

    # ── Tips ─────────────────────────────────────────────────────
    add_heading(doc, "Strategic Advice for Single Business Mode", level=2)

    add_bullet(doc,
        "Understand your stakeholder map early. In Single Business Mode, stakeholder "
        "salience is concentrated — you have fewer but more contextually powerful "
        "stakeholders than in the conglomerate. A hostile Host Government in Africa or "
        "a hostile SEBI regulator in South Asia can materially affect your terminal valuation.")
    add_bullet(doc,
        "Your industry-specific pillar is your identity. Investors, regulators, and "
        "community leaders watch your industry pillar decisions most closely. Consistent "
        "leadership choices in this area build a durable stakeholder alliance.")
    add_bullet(doc,
        "Regional black swans are correlated with neglect. The probability of a regional "
        "black swan increases if your community trust is low. Invest in social licence early "
        "to reduce your exposure.")
    add_bullet(doc,
        "Think about your ESG reporting framework from Round 1. If you are in Europe, "
        "the CSRD requires supply chain due diligence — your Supply Chain pillar choices "
        "will directly affect your end-game reporting score. Know your framework.")
    add_bullet(doc,
        "The Stakeholder Sentiment panel is a leading indicator. Changes in attitude scores "
        "in one round predict crisis events in the next. Monitor it after every decision.")


# ═════════════════════════════════════════════════════════════════
#  FACILITATOR SECTION
# ═════════════════════════════════════════════════════════════════

def add_facilitator_section(doc):
    doc.add_page_break()

    add_heading(doc, "Facilitator Module: Single Business Mode & Regional Localisation", level=1)

    add_body(doc,
        "Single Business Mode transforms Muressons from a generic conglomerate simulation into a "
        "precision-targeted learning experience calibrated to a specific industry vertical and "
        "geographic region. This module covers everything you need to: configure a Single Business "
        "cohort, manage regional stakeholder and pillar data, monitor live stakeholder sentiment, "
        "and use the industry benchmark comparison tool in debrief."
    )

    # ── Pedagogical Design ───────────────────────────────────────
    add_heading(doc, "Pedagogical Design Intent", level=2)

    add_body(doc, "Single Business Mode operationalises four learning objectives not achievable in the standard conglomerate format:")

    add_bullet(doc,
        "Industry Materiality Fluency — Students engage with ESG issues that are specifically "
        "material to their assigned industry. An Agriculture student grappling with Water "
        "Stewardship decisions, or a Technology student navigating Data Privacy & Ethics, "
        "develops sector-specific ESG reasoning rather than generic trade-off thinking.")
    add_bullet(doc,
        "Regional Regulatory Context — Students experience the regulatory pressure of a "
        "specific jurisdiction. SEBI BRSR requirements, CSRD obligations, SEC climate "
        "disclosure rules, and ASEAN taxonomy criteria are not abstract — they manifest "
        "as black swan events, penalty mechanics, and terminal valuation adjustments.")
    add_bullet(doc,
        "Stakeholder Salience in Context — With 5–8 regionally specific stakeholders rather "
        "than a generic global set, students must reason about power, legitimacy, and urgency "
        "in a concrete setting. A South Asian Smallholder Farmer collective has a different "
        "salience profile than a European Consumer NGO.")
    add_bullet(doc,
        "Comparative Industry Benchmarking — The industry benchmark tool allows post-game "
        "comparison against sector P25/P50/P75 thresholds, making the debrief "
        "concrete and enabling cross-cohort discussions about sector-relative performance.")

    # ── Cohort Formation ─────────────────────────────────────────
    add_heading(doc, "Setting Up a Single Business Cohort", level=2)

    add_body(doc,
        "When creating a new cohort in the Facilitator Dashboard or God Mode, you will see "
        "an expanded Create Cohort form with simulation mode and regional options."
    )

    add_image(doc, "single_bu_create_cohort.png", width_inches=5.5,
              caption="Figure: Create Cohort form in Single Business Mode — "
                      "showing mode toggle, vertical selector, and mandatory region dropdown.")

    add_heading(doc, "Step-by-Step: Creating a Single Business Cohort", level=3)

    add_bullet(doc, "Step 1 — Simulation Mode: Toggle to 'Single Business'. The BU composition accordion collapses.")
    add_bullet(doc, "Step 2 — Industry Vertical: Select the sector for this cohort (Agriculture, Banking & Finance, Oil & Gas, Retail FMCG, Technology, Pharma / Healthcare).")
    add_bullet(doc, "Step 3 — Geographic Region: Select a region (mandatory — cohort cannot be created without this). Options: ASEAN, South Asia, Europe, North America, Africa.")
    add_bullet(doc, "Step 4 — Cohort Name & Standard fields: Complete as normal.")
    add_bullet(doc, "Step 5 — Create. The system will automatically load the industry+region stakeholder profile and activate region-specific black swan events.")

    add_info_box(doc,
        "ℹ️  You can override a player's region after cohort creation via the Player Registry "
        "→ Induct Player panel. This is useful if one player is studying a cross-regional "
        "operation scenario while the rest of the cohort focuses on the cohort region."
    )

    doc.add_paragraph()

    # ── 4-BU Conglomerate Per-BU Regions ─────────────────────────
    add_heading(doc, "Multi-Region Conglomerate Mode", level=2)

    add_body(doc,
        "In the standard 4-BU Conglomerate mode, you can assign a different geographic region "
        "to each BU slot. This models a real multinational with divisions operating across "
        "different regulatory environments — for example, Pharma in Europe (CSRD), "
        "Electronics in ASEAN (ASEAN Taxonomy), Consumer Goods in Africa (GRI/King IV), "
        "and Software in North America (SEC)."
    )

    add_body(doc,
        "To configure per-BU regions: in the Create Cohort form with 'Conglomerate' mode selected, "
        "expand the BU Composition accordion. Each BU slot will display its own region dropdown. "
        "After cohort creation, you can update per-BU regions via:"
    )

    add_bullet(doc, "Facilitator Dashboard → Session Controls → BU Composition → set bu_regions per slot")
    add_bullet(doc, "God Mode → Cohort Orchestration → BU Composition editor")

    doc.add_paragraph()

    # ── Stakeholder Configuration ─────────────────────────────────
    add_heading(doc, "God Mode: Stakeholder Configurator", level=2)

    add_body(doc,
        "The Stakeholder Configurator (God Mode → Engine Configuration → 👥 Stakeholder Config) "
        "allows you to view and edit the stakeholder profiles for any region. Stakeholder data "
        "is stored in JSON files per region and is automatically loaded when a player session "
        "starts in that region."
    )

    add_image(doc, "single_bu_stakeholder_config.png", width_inches=5.5,
              caption="Figure: Stakeholder Configurator — Oil & Gas / Africa configuration "
                      "showing Host Government, Community Leader, and NGO Monitor profiles.")

    add_heading(doc, "Stakeholder Profile Fields", level=3)

    field_tbl = doc.add_table(rows=1, cols=3)
    field_tbl.style = 'Table Grid'
    add_table_header(field_tbl, "Field", "Options", "Purpose")
    add_table_row(field_tbl, "Power", "High / Medium / Low", "Mitchell-Agle-Wood salience weighting")
    add_table_row(field_tbl, "Interest", "High / Medium / Low", "Attention to the company's decisions")
    add_table_row(field_tbl, "Quadrant", "Manage Closely / Keep Satisfied / Keep Informed / Monitor", "Mendelow positioning")
    add_table_row(field_tbl, "Urgency", "Checkbox", "Marks time-sensitive claims")
    add_table_row(field_tbl, "Legitimacy", "Checkbox", "Marks stakeholders with recognised authority")
    add_table_row(field_tbl, "Engagement Tactics", "List of options (min 2)", "Decision choices shown to players in stakeholder exercises")

    doc.add_paragraph()

    add_bold_body(doc,
        "Salience Score: ",
        "The sentiment engine weights each stakeholder's attitude impact by salience = "
        "Power × Urgency × Legitimacy (Mitchell-Agle-Wood model). A stakeholder with all "
        "three attributes is 'Definitive' — their attitude swings have the strongest effect "
        "on group reputation and regional risk scores."
    )

    # ── Pillar Configurator ───────────────────────────────────────
    add_heading(doc, "God Mode: Pillar Configurator", level=2)

    add_body(doc,
        "The Pillar Configurator (God Mode → Engine Configuration → 🏛️ Pillar Configurator) "
        "allows you to view and manage industry-specific pillar overrides and add custom "
        "strategic decision areas for any vertical."
    )

    add_image(doc, "single_bu_pillar_configurator.png", width_inches=5.5,
              caption="Figure: Pillar Configurator for the Technology vertical — showing the "
                      "standard areas (left), the 🔒 Data Privacy & Ethics override (centre), "
                      "and a custom 🧠 AI Governance area (right).")

    add_heading(doc, "Three-Column Architecture", level=3)

    add_bullet(doc,
        "Standard Areas (left): The 5 canonical pillar areas (Energy, Operations, Supply Chain, "
        "Offsetting, HR). These are read-only — they are defined globally and available in every session.")
    add_bullet(doc,
        "Override Areas (centre): Industry-specific replacements for standard areas. "
        "For example, 'Data Privacy & Ethics' replaces 'Operations' for Technology verticals. "
        "Pre-loaded for all 6 verticals. Edit via the JSON file or through future admin UI.")
    add_bullet(doc,
        "Custom Areas (right): Additional pillar areas you create for this vertical. "
        "These are appended after the standard/override areas. Use this to add emerging "
        "topics or institution-specific ESG themes.")

    add_heading(doc, "Adding a Custom Pillar Area", level=3)

    add_bullet(doc, "Click '+ Add Custom Area'")
    add_bullet(doc, "Enter: Area Key (unique slug, e.g. 'ai_governance'), Label, Icon emoji, Display Order")
    add_bullet(doc, "Add at least 2 options (Option A, Option B, Option C) with labels, rationale, costs, and flag names")
    add_bullet(doc, "Save — the area immediately becomes available for sessions using that vertical")

    add_info_box(doc,
        "💡 Facilitator Tip: Custom pillar areas let you tailor the simulation to your institution's "
        "specific curriculum. For example, a South Asian business school running an Agriculture "
        "cohort might add a 'Crop Insurance & Climate Adaptation' pillar to reflect PMFBY scheme decisions."
    )

    doc.add_paragraph()

    # ── Stakeholder Sentiment Live Monitoring ─────────────────────
    add_heading(doc, "Live Stakeholder Sentiment Monitoring", level=2)

    add_body(doc,
        "After each round, the simulation's sentiment engine updates every stakeholder's attitude "
        "score deterministically based on the decisions made. The Stakeholder Sentiment Panel "
        "is available in the Session Viewer and the Executive Cockpit analytics sidebar."
    )

    add_image(doc, "single_bu_sentiment_panel.png", width_inches=5.5,
              caption="Figure: Stakeholder Sentiment Panel (Round 4) — showing attitude scores, "
                      "round-on-round deltas, salience badges, and sentiment narratives.")

    add_heading(doc, "How the Sentiment Engine Works", level=3)

    add_body(doc,
        "The engine is fully deterministic — no AI/LLM is used. It operates on a rule table that "
        "maps decision flags to attitude deltas per stakeholder type:"
    )

    rule_tbl = doc.add_table(rows=1, cols=3)
    rule_tbl.style = 'Table Grid'
    add_table_header(rule_tbl, "Decision Flag (example)", "Stakeholder Type", "Attitude Delta")
    add_table_row(rule_tbl, "renewable_ppa_signed",       "Regulator",          "+8")
    add_table_row(rule_tbl, "renewable_ppa_signed",       "Community Leader",   "+5")
    add_table_row(rule_tbl, "zero_investment_round",      "ESG Investor",       "−10")
    add_table_row(rule_tbl, "whistleblower_scandal (🦢)",  "All Stakeholders",  "−20")
    add_table_row(rule_tbl, "circular_redesign",          "NGO Monitor",        "+12")
    add_table_row(rule_tbl, "resource_nationalisation_bs", "Host Government",   "−15")

    doc.add_paragraph()

    add_bold_body(doc,
        "Debrief Use: ",
        "Show the sentiment panel's round-by-round history in debrief. Ask students: "
        "'Which stakeholder deteriorated fastest, and in which round?' Then trace back "
        "to the specific pillar choice that triggered the decline. This creates a "
        "'decision archaeology' discussion that connects choices to long-run relationship outcomes."
    )

    # ── Industry Benchmarks ───────────────────────────────────────
    add_heading(doc, "Industry Benchmark Comparison Tool", level=2)

    add_body(doc,
        "The Industry Benchmark panel (available via the admin API: "
        "GET /api/admin/{session_id}/industry-benchmark) compares a team's final KPIs "
        "against sector percentile benchmarks for their assigned vertical."
    )

    add_image(doc, "single_bu_benchmark_panel.png", width_inches=5.5,
              caption="Figure: Industry Benchmark Comparison — Oil & Gas / Africa. "
                      "Showing player position vs. P25, Median (P50), and P75 benchmarks "
                      "across Carbon Intensity, Social License, Governance Risk, and EBITDA Margin.")

    add_heading(doc, "Available Benchmark Verticals", level=3)

    bench_tbl = doc.add_table(rows=1, cols=3)
    bench_tbl.style = 'Table Grid'
    add_table_header(bench_tbl, "Vertical", "Carbon Intensity P50", "Social License P50")
    add_table_row(bench_tbl, "🌾 Agriculture",          "32 tCO₂/unit", "68/100")
    add_table_row(bench_tbl, "🏦 Banking & Finance",    "12 tCO₂/unit", "72/100")
    add_table_row(bench_tbl, "⛽ Oil & Gas",            "55 tCO₂/unit", "58/100")
    add_table_row(bench_tbl, "🛒 Retail / FMCG",       "28 tCO₂/unit", "70/100")
    add_table_row(bench_tbl, "💻 Technology",           "18 tCO₂/unit", "75/100")
    add_table_row(bench_tbl, "💊 Pharma / Healthcare",  "22 tCO₂/unit", "74/100")

    doc.add_paragraph()

    add_bold_body(doc,
        "Debrief Suggestion: ",
        "Display the benchmark panel for each team simultaneously in the final debrief. "
        "Ask: 'Which team is sector-competitive? Which team has a carbon intensity that "
        "would trigger a CBAM surcharge or an SEC disclosure flag?' "
        "This ground-truths the simulation in real industry data and makes the "
        "'so what?' question viscerally clear."
    )

    # ── Regional ESG Report ───────────────────────────────────────
    add_heading(doc, "Regional ESG Report Generator", level=2)

    add_body(doc,
        "After a session is complete, you can generate a region-aligned ESG report via "
        "the admin API or the Reports Export panel. The report maps the team's decisions "
        "to the disclosure requirements of their assigned region's primary framework."
    )

    report_tbl = doc.add_table(rows=1, cols=3)
    report_tbl.style = 'Table Grid'
    add_table_header(report_tbl, "Region", "Framework", "Key Report Sections")
    add_table_row(report_tbl, "South Asia", "SEBI BRSR",
        "NGRBC Principle mapping, Essential vs Leadership indicator audit, ₹ compliance costs")
    add_table_row(report_tbl, "Europe", "CSRD / ESRS",
        "Double materiality matrix, ESRS disclosure topics, CSRD transition plan readiness")
    add_table_row(report_tbl, "North America", "SEC / TCFD",
        "Scope 1/2/3 emissions, climate risk scenario analysis, governance disclosures")
    add_table_row(report_tbl, "ASEAN", "ASEAN Taxonomy",
        "Traffic light classification (Green/Amber/Red), transition activities, social safeguards")
    add_table_row(report_tbl, "Africa", "GRI + King IV",
        "Stakeholder inclusivity, integrated value creation, King IV governance principles")

    doc.add_paragraph()

    # ── Facilitator Controls Reference ────────────────────────────
    add_heading(doc, "Facilitator Controls Reference — New Features", level=2)

    ctrl_tbl = doc.add_table(rows=1, cols=3)
    ctrl_tbl.style = 'Table Grid'
    add_table_header(ctrl_tbl, "Feature", "Location", "Access Level")
    add_table_row(ctrl_tbl, "Set cohort mode (Single BU / Conglomerate)",
        "Create Cohort modal", "Lead Facilitator, Super Admin")
    add_table_row(ctrl_tbl, "Set industry vertical",
        "Create Cohort modal", "Lead Facilitator, Super Admin")
    add_table_row(ctrl_tbl, "Set cohort region (mandatory)",
        "Create Cohort modal", "Lead Facilitator, Super Admin")
    add_table_row(ctrl_tbl, "Override player region individually",
        "Player Registry → Induct Player", "Lead Facilitator, Super Admin")
    add_table_row(ctrl_tbl, "Set per-BU region (conglomerate mode)",
        "BU Composition editor", "Lead Facilitator, Super Admin")
    add_table_row(ctrl_tbl, "Edit regional stakeholder profiles",
        "God Mode → Stakeholder Config", "Super Admin only")
    add_table_row(ctrl_tbl, "Add/edit custom pillar areas",
        "God Mode → Pillar Configurator", "Super Admin only")
    add_table_row(ctrl_tbl, "View stakeholder sentiment history",
        "Session Viewer → Sentiment tab", "All facilitators")
    add_table_row(ctrl_tbl, "View industry benchmark comparison",
        "Session Viewer → Benchmark tab", "All facilitators")
    add_table_row(ctrl_tbl, "Generate regional ESG report",
        "Reports Export → Regional ESG", "All facilitators")
    add_table_row(ctrl_tbl, "View cohort Industry × Region diversity",
        "Platform Analytics → Cohort Diversity", "Lead Facilitator, Super Admin")

    doc.add_paragraph()

    # ── Cohort Diversity ─────────────────────────────────────────
    add_heading(doc, "Cohort Diversity — Industry × Region Heatmap", level=2)

    add_body(doc,
        "The Cohort Diversity panel (Platform Analytics → Cohort Diversity) shows a heatmap "
        "of how players in a cohort are distributed across Industry Verticals and Geographic "
        "Regions. This is particularly useful when running mixed-mode cohorts where different "
        "players are assigned different verticals or regions."
    )

    add_bullet(doc,
        "Rows = Industry Verticals (Agriculture, Banking, Oil & Gas, Retail, Technology, Pharma)")
    add_bullet(doc,
        "Columns = Geographic Regions (ASEAN, South Asia, Europe, North America, Africa)")
    add_bullet(doc,
        "Cell value = number of players in that Industry × Region combination")
    add_bullet(doc,
        "Click any cell to see the player IDs assigned to that combination")

    add_bold_body(doc,
        "Use Case: ",
        "If you are running a global executive education programme with participants from "
        "different regions, assign each participant to their own industry and region. "
        "The cohort diversity heatmap then becomes a real-time view of the classroom's "
        "geographic and sectoral distribution — a conversation starter for cross-regional "
        "sustainability comparison."
    )

    doc.add_paragraph()

    # ── Common Facilitation Questions ────────────────────────────
    add_heading(doc, "Common Facilitation Questions", level=2)

    add_bold_body(doc, "Q: Can I run a single business session alongside a standard 4-BU session in the same class?")
    add_body(doc,
        "Yes. Each cohort's mode is set independently. You can have some teams running "
        "as conglomerates and others as single businesses simultaneously. The facilitator "
        "dashboard aggregates them all in the leaderboard."
    )

    add_bold_body(doc, "Q: What if no stakeholder config exists for my chosen Industry + Region combination?")
    add_body(doc,
        "The system uses a three-level fallback: Industry + Region → Industry only → "
        "the standard global stakeholder set. You will see a console warning, but the "
        "session will launch normally. Use the Stakeholder Configurator in God Mode to "
        "create the missing configuration."
    )

    add_bold_body(doc, "Q: Can I add a custom region?")
    add_body(doc,
        "The five supported regions (ASEAN, South Asia, Europe, North America, Africa) are "
        "hardcoded in the current version. Adding a new region requires creating JSON data files "
        "for stakeholder configs and pillar overrides, and adding the region to the "
        "VALID_REGIONS validation set in admin_router.py. Contact your system administrator."
    )

    add_bold_body(doc, "Q: The region-specific black swan didn't fire. Is that expected?")
    add_body(doc,
        "Yes — all black swans are probabilistic. A region-specific event has a base probability "
        "of approximately 9–12% per eligible round. It is possible to complete the simulation "
        "without one triggering. However, if the team's governance risk is high or community "
        "trust is low, the probability is modified upward. Consider triggering a black swan "
        "manually via the Crisis Overrides panel if you want to ensure students experience it."
    )


# ═════════════════════════════════════════════════════════════════
#  RUNNER
# ═════════════════════════════════════════════════════════════════

def process(input_path, output_path, add_fn, label):
    if not os.path.exists(input_path):
        print(f"[ERROR] Not found: {input_path}")
        return
    doc = docx.Document(input_path)
    add_fn(doc)
    doc.save(output_path)
    size_mb = os.path.getsize(output_path) / 1_048_576
    print(f"[OK] {label} -> {os.path.basename(output_path)}  ({size_mb:.1f} MB)")


if __name__ == '__main__':
    process(STUDENT_IN,     STUDENT_OUT,     add_player_section,     "Player Manual (v7)")
    process(FACILITATOR_IN, FACILITATOR_OUT, add_facilitator_section, "Facilitator Manual (v7)")
    print("\nDone. Both manuals saved.")
