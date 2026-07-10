"""Shared styles and helpers for the DOCX generator."""
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import re, os

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), 'screenshots')

# Map caption keywords to screenshot filenames
SCREENSHOT_MAP = {
    'Executive Cockpit': 's05_executive_cockpit.png',
    'initial state': 's05_executive_cockpit.png',
    'landing': 's01_landing.png',
    'Round Briefing': 's02_round_briefing.png',
    'Stakeholder Map modal': 's04_stakeholder_map.png',
    'stakeholder cards': 's04_stakeholder_map.png',
    'Stakeholder Map gate': 's03_stakeholder_gate.png',
    'CSRD Materiality Matrix': 's03_stakeholder_gate.png',
    'Advanced Metrics': 's06_advanced_metrics.png',
    'Synergy': 's06_advanced_metrics.png',
    'Dashboard Home': 's10_dashboard_home2.png',
    'summary cards': 's10_dashboard_home2.png',
    'Teleprompter': 's11_teleprompter.png',
    'presenter mode': 's11_teleprompter.png',
    'Leaderboard': 's12_leaderboard.png',
    'sortable columns': 's12_leaderboard.png',
    'Player Registry': 's13_player_registry.png',
    'connection status': 's13_player_registry.png',
    'Team Impersonation': 's14_impersonation.png',
    'student cockpit': 's14_impersonation.png',
    'Cohort Analytics': 's15_cohort_analytics.png',
    'Decision Heatmap': 's15_cohort_analytics.png',
    'Decision History': 's16_decision_history.png',
    'Teaching Journal': 's17_teaching_journal.png',
    'annotations': 's17_teaching_journal.png',
    'onboarding': 's18_onboarding.png',
    'Consequence DNA': 's06_advanced_metrics.png',
    'Shadow Board': 's02_round_briefing.png',
    'Final Report': 's05_executive_cockpit.png',
    'Side Track': 's07_dashboard_home.png',
    'Autonomous Stakeholders': 's06_advanced_metrics.png',
    'God Mode': 's08_sidebar_analytics.png',
    'System Overview': 's08_sidebar_analytics.png',
    'scaffolding': 's08_sidebar_analytics.png',
    'Facilitator Registry': 's13_player_registry.png',
    'role management': 's13_player_registry.png',
    'Macro Economics': 's09_sidebar_config.png',
    'engine tunables': 's09_sidebar_config.png',
    'Auto-Pause': 's09_sidebar_config.png',
    'Swipe File': 's14_impersonation.png',
    'message templates': 's14_impersonation.png',
    'DNA Comparison': 's06_advanced_metrics.png',
    'Export Reports': 's16_decision_history.png',
    'Sustainability Balanced Scorecard': 's06_advanced_metrics.png',
    'Market Feed': 's05_executive_cockpit.png',
    'Vertical': 's09_sidebar_config.png',
    'architecture flowchart': 's00_architecture.png',
    'Simulation Architecture': 's00_architecture.png',
}

BRAND_NAVY = RGBColor(0x0F, 0x17, 0x2A)
BRAND_BLUE = RGBColor(0x3B, 0x82, 0xF6)
BRAND_TEAL = RGBColor(0x06, 0xB6, 0xD4)
BRAND_GREEN = RGBColor(0x22, 0xC5, 0x5E)
BRAND_RED = RGBColor(0xEF, 0x44, 0x44)
BRAND_AMBER = RGBColor(0xF5, 0x9E, 0x0B)
BRAND_GRAY = RGBColor(0x6B, 0x72, 0x80)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF3, 0xF4, 0xF6)

def setup_doc():
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(10.5)
    font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
    pf = style.paragraph_format
    pf.space_after = Pt(6)
    pf.line_spacing = 1.15

    for level in range(1, 5):
        name = f'Heading {level}'
        h = doc.styles[name]
        h.font.name = 'Calibri'
        h.font.bold = True
        h.font.color.rgb = BRAND_NAVY
        if level == 1:
            h.font.size = Pt(22)
            h.paragraph_format.space_before = Pt(24)
            h.paragraph_format.space_after = Pt(12)
        elif level == 2:
            h.font.size = Pt(16)
            h.paragraph_format.space_before = Pt(18)
            h.paragraph_format.space_after = Pt(8)
        elif level == 3:
            h.font.size = Pt(13)
            h.font.color.rgb = BRAND_BLUE
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(6)
        else:
            h.font.size = Pt(11)
            h.font.color.rgb = BRAND_TEAL
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
        # Add footer
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.text = "Muressons Facilitator Manual — Project Equilibrium — CONFIDENTIAL"
        fp.style.font.size = Pt(7)
        fp.style.font.color.rgb = BRAND_GRAY
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    return doc

def add_styled_table(doc, headers, rows, col_widths=None):
    """Add a formatted table with header row."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    
    # Header row
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.runs[0] if p.runs else p.add_run(h)
        run.font.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = WHITE
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="0F172A"/>')
        cell._tc.get_or_add_tcPr().append(shading)
    
    # Data rows
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = table.rows[ri + 1].cells[ci]
            cell.text = str(val)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(2)
                for r in p.runs:
                    r.font.size = Pt(9)
            if ri % 2 == 1:
                shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F3F4F6"/>')
                cell._tc.get_or_add_tcPr().append(shading)
    
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Inches(w)
    
    doc.add_paragraph()
    return table

def add_callout(doc, text, style="important"):
    """Add a styled callout box."""
    icons = {"important": "⚠️ IMPORTANT", "warning": "🚫 DO NOT REVEAL", "tip": "💡 TIP", "note": "📌 NOTE"}
    p = doc.add_paragraph()
    run = p.add_run(f"  {icons.get(style, 'NOTE')}: ")
    run.font.bold = True
    run.font.size = Pt(9.5)
    run.font.color.rgb = BRAND_RED if style in ("warning", "important") else BRAND_BLUE
    run2 = p.add_run(text)
    run2.font.size = Pt(9.5)
    run2.font.italic = True

def add_screenshot_placeholder(doc, caption):
    """Embed a real screenshot if available, otherwise show placeholder text."""
    # Find matching screenshot by caption keywords
    matched_file = None
    for keyword, filename in SCREENSHOT_MAP.items():
        if keyword.lower() in caption.lower():
            filepath = os.path.join(SCREENSHOT_DIR, filename)
            if os.path.exists(filepath):
                matched_file = filepath
                break
    
    if matched_file:
        # Embed actual screenshot
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(matched_file, width=Inches(5.8))
        # Caption below image
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run(f"Figure: {caption}")
        r.font.size = Pt(8.5)
        r.font.italic = True
        r.font.color.rgb = BRAND_GRAY
        cap.paragraph_format.space_after = Pt(12)
    else:
        # Fallback placeholder
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"[SCREENSHOT: {caption}]")
        run.font.size = Pt(10)
        run.font.color.rgb = BRAND_TEAL
        run.font.italic = True

def add_page_break(doc):
    doc.add_page_break()

def add_bullet_list(doc, items, bold_prefix=False):
    for item in items:
        p = doc.add_paragraph(style='List Bullet')
        if bold_prefix and ': ' in item:
            parts = item.split(': ', 1)
            run = p.add_run(parts[0] + ': ')
            run.font.bold = True
            run.font.size = Pt(10)
            run2 = p.add_run(parts[1])
            run2.font.size = Pt(10)
            # Clear default text
            p.clear()
            p.add_run(parts[0] + ': ').font.bold = True
            p.runs[0].font.size = Pt(10)
            r2 = p.add_run(parts[1])
            r2.font.size = Pt(10)
        else:
            p.clear()
            r = p.add_run(item)
            r.font.size = Pt(10)
