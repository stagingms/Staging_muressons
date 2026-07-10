"""
Generate a polished PowerPoint player briefing for the Muressons Simulation.
Uses existing guide_images/ screenshots and python-pptx.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# -- Paths --
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "guide_images")
OUTPUT = os.path.join(SCRIPT_DIR, "Muressons_Player_Briefing.pptx")

# -- 16:9 Layout Constants --
SLIDE_W = 13.333
SLIDE_H = 7.5
MARGIN = 0.5
CONTENT_W = SLIDE_W - 2 * MARGIN   # ~12.333
HALF_W = (CONTENT_W - 0.4) / 2     # ~5.97 each half-column
RIGHT_X = MARGIN + HALF_W + 0.4    # ~6.87 right column start
CARD_FULL_W = CONTENT_W            # full-width card

# -- Brand palette --
DARK_BG       = RGBColor(0x0B, 0x14, 0x1F)
ACCENT_TEAL   = RGBColor(0x00, 0xD4, 0xAA)
ACCENT_GOLD   = RGBColor(0xD4, 0xA5, 0x1A)
WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GREY    = RGBColor(0xB0, 0xBC, 0xCB)
MID_GREY      = RGBColor(0x6B, 0x7B, 0x8D)
CARD_BG       = RGBColor(0x13, 0x1F, 0x2E)
DANGER_RED    = RGBColor(0xE8, 0x4D, 0x4D)
SUCCESS_GREEN = RGBColor(0x2E, 0xCC, 0x71)


def add_dark_background(slide):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = DARK_BG


def add_shape_rect(slide, left, top, width, height, fill_color, border_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


def add_text_box(slide, left, top, width, height, text, font_size=18,
                 color=WHITE, bold=False, alignment=PP_ALIGN.LEFT, font_name="Calibri"):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def add_multiline_text(slide, left, top, width, height, lines, font_size=14,
                       color=WHITE, font_name="Calibri", line_spacing=1.5,
                       alignment=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True

    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = alignment
        p.space_after = Pt(4)

        if isinstance(line, tuple):
            text, bold, clr = line
        else:
            text, bold, clr = line, False, color

        run = p.add_run()
        run.text = text
        run.font.size = Pt(font_size)
        run.font.color.rgb = clr
        run.font.bold = bold
        run.font.name = font_name

    return txBox


def add_accent_line(slide, left, top, width, color=ACCENT_TEAL):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Pt(3))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_image_safe(slide, img_name, left, top, width=None, height=None):
    path = os.path.join(IMG_DIR, img_name)
    if not os.path.exists(path):
        print(f"  [!] Image not found: {path}")
        return None
    kwargs = {"image_file": path, "left": left, "top": top}
    if width:
        kwargs["width"] = width
    if height:
        kwargs["height"] = height
    return slide.shapes.add_picture(**kwargs)


def add_rounded_card(slide, left, top, width, height, fill_color=CARD_BG, border_color=ACCENT_TEAL):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1)
    return shape


def add_number_circle(slide, x, y, num, accent):
    """Add a filled circle with a number inside."""
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, Inches(0.45), Inches(0.45))
    circle.fill.solid()
    circle.fill.fore_color.rgb = accent
    circle.line.fill.background()
    tf = circle.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = str(num)
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.color.rgb = DARK_BG


# =====================================================================
# SLIDE BUILDERS
# =====================================================================

def slide_title(prs):
    """Slide 1: Title slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    cx = SLIDE_W / 2  # center x
    line_w = 6.0

    add_accent_line(slide, Inches(cx - line_w / 2), Inches(2.0), Inches(line_w))

    add_text_box(slide, Inches(MARGIN), Inches(2.2), Inches(CONTENT_W), Inches(1),
                 "MURESSONS GLOBAL", font_size=48, color=ACCENT_TEAL,
                 bold=True, alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Inches(MARGIN), Inches(3.1), Inches(CONTENT_W), Inches(0.6),
                 "CORPORATE SUSTAINABILITY SIMULATION", font_size=24,
                 color=ACCENT_GOLD, bold=False, alignment=PP_ALIGN.CENTER)

    add_accent_line(slide, Inches(cx - line_w / 2), Inches(3.8), Inches(line_w))

    add_text_box(slide, Inches(1), Inches(4.3), Inches(SLIDE_W - 2), Inches(0.5),
                 "Player Briefing  |  10 Rounds  ·  5 Years  ·  4 Business Units",
                 font_size=18, color=LIGHT_GREY, alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Inches(1), Inches(6.5), Inches(SLIDE_W - 2), Inches(0.4),
                 "Sovereign Intelligence Systems  ·  Executive Education",
                 font_size=12, color=MID_GREY, alignment=PP_ALIGN.CENTER)


def slide_overview(prs):
    """Slide 2: What is Muressons?"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "WHAT IS MURESSONS?", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    lines = [
        ("You are a newly appointed Board Director of Muressons Group --", True, WHITE),
        ("a multinational conglomerate with four business units.", False, LIGHT_GREY),
        ("", False, WHITE),
        ("Your mission:", True, ACCENT_GOLD),
        ("Navigate 10 rounds of ESG crises, investment trade-offs,", False, LIGHT_GREY),
        ("and stakeholder dynamics across 5 simulated years.", False, LIGHT_GREY),
        ("", False, WHITE),
        ("Each round represents a 6-month semester. You will:", True, WHITE),
        ("  *  Read crisis briefings from the Board", False, LIGHT_GREY),
        ("  *  Choose strategic responses (A, B, or C)", False, LIGHT_GREY),
        ("  *  Allocate capital across four business units", False, LIGHT_GREY),
        ("  *  Manage financial and sustainability KPIs", False, LIGHT_GREY),
        ("  *  Compete against peers on a live leaderboard", False, LIGHT_GREY),
        ("", False, WHITE),
        ("Your performance is measured by Terminal Valuation --", True, WHITE),
        ("a formula that rewards both profit AND sustainability.", False, ACCENT_TEAL),
    ]
    add_multiline_text(slide, Inches(MARGIN), Inches(1.2), Inches(CONTENT_W), Inches(5.5),
                       lines, font_size=16, line_spacing=1.4)


def slide_business_units(prs):
    """Slide 3: The Four Business Units."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "YOUR FOUR BUSINESS UNITS", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    bus = [
        ("PHARMA", "Rev: $18.0M  |  Margin: 36.1%",
         "High-margin pharmaceutical division.\nGovernance risk: 15%. Highest revenue\nbut exposed to regulatory compliance\nand social license pressures.",
         RGBColor(0x2E, 0xCC, 0x71)),
        ("ELECTRONICS", "Rev: $16.5M  |  Margin: 34.5%",
         "Technology and electronic components.\nGovernance risk: 20%. Carbon-intensive\nmanufacturing with supply chain\ncomplexity and AI ethics exposure.",
         RGBColor(0x33, 0x98, 0xDB)),
        ("CONSUMER GOODS", "Rev: $10.5M  |  Margin: 25.7%",
         "Fast-moving consumer products.\nGovernance risk: 10%. Lower margins\nbut broad social license and circular\neconomy transition opportunities.",
         RGBColor(0xF3, 0x9C, 0x12)),
        ("SOFTWARE", "Rev: $8.5M  |  Margin: 50.6%",
         "Digital services and SaaS platform.\nGovernance risk: 8%. Highest margins,\nlowest carbon intensity, but vulnerable\nto AI bias and data governance crises.",
         RGBColor(0x9B, 0x59, 0xB6)),
    ]

    card_w = Inches(HALF_W)
    card_h = Inches(2.5)
    gap = 0.4
    positions = [
        (Inches(MARGIN), Inches(1.3)),
        (Inches(RIGHT_X), Inches(1.3)),
        (Inches(MARGIN), Inches(4.1)),
        (Inches(RIGHT_X), Inches(4.1)),
    ]

    for i, (name, subtitle, desc, accent) in enumerate(bus):
        left, top = positions[i]
        add_rounded_card(slide, left, top, card_w, card_h, CARD_BG, accent)
        add_text_box(slide, left + Inches(0.25), top + Inches(0.15), card_w - Inches(0.5), Inches(0.4),
                     name, font_size=20, color=accent, bold=True)
        add_text_box(slide, left + Inches(0.25), top + Inches(0.55), card_w - Inches(0.5), Inches(0.3),
                     subtitle, font_size=12, color=LIGHT_GREY)
        add_text_box(slide, left + Inches(0.25), top + Inches(0.95), card_w - Inches(0.5), Inches(1.4),
                     desc, font_size=12, color=WHITE)


def slide_login(prs):
    """Slide 4: Getting Started."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "GETTING STARTED", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    steps = [
        ("1.", "Enter your Executive Identifier (Player ID)", "  e.g. MUR-001"),
        ("2.", "Enter your Clearance Cipher (Password)", "  Provided by your facilitator"),
        ("3.", "Click 'Establish Link' to join your cohort", "  Or 'Start Solo Session' to practise alone"),
    ]

    y = Inches(1.2)
    for num, main, sub in steps:
        add_text_box(slide, Inches(MARGIN), y, Inches(0.5), Inches(0.3),
                     num, font_size=18, color=ACCENT_GOLD, bold=True)
        add_text_box(slide, Inches(MARGIN + 0.5), y, Inches(4.5), Inches(0.3),
                     main, font_size=15, color=WHITE, bold=True)
        add_text_box(slide, Inches(MARGIN + 0.5), y + Inches(0.3), Inches(4.5), Inches(0.25),
                     sub, font_size=12, color=LIGHT_GREY)
        y += Inches(0.7)

    # Screenshot on the right
    add_image_safe(slide, "login_screen.png", Inches(RIGHT_X), Inches(1.1),
                   width=Inches(HALF_W), height=Inches(3.5))

    # Tip card at bottom
    add_rounded_card(slide, Inches(MARGIN), Inches(5.5), Inches(CARD_FULL_W), Inches(1.0),
                     CARD_BG, ACCENT_GOLD)
    add_text_box(slide, Inches(MARGIN + 0.3), Inches(5.6), Inches(CARD_FULL_W - 0.6), Inches(0.8),
                 "TIP: The simulation URL is http://localhost:3000 (or the IP address shown by your facilitator). "
                 "Keep your Player ID handy -- you'll need it to rejoin if disconnected.",
                 font_size=13, color=LIGHT_GREY)


def slide_cockpit(prs):
    """Slide 5: The Executive Cockpit."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "THE EXECUTIVE COCKPIT", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.4),
                 "This is your command centre. The 3-panel layout gives you everything you need:",
                 font_size=15, color=LIGHT_GREY)

    # Screenshot (full width)
    add_image_safe(slide, "cockpit.png", Inches(MARGIN), Inches(1.6),
                   width=Inches(CARD_FULL_W), height=Inches(3.8))

    # Three column labels at bottom
    third_w = (CARD_FULL_W - 0.6) / 3
    labels = [
        ("LEFT PANEL", "KPI Dashboard\nFinancials, Charts, Metrics"),
        ("CENTRE PANEL", "Briefing + Decisions\nCrisis, Strategy, Allocation"),
        ("RIGHT PANEL", "Intel & Comms\nMailbox, Market Feed, AI Advisor"),
    ]

    for i, (title, desc) in enumerate(labels):
        x = Inches(MARGIN + i * (third_w + 0.3))
        add_rounded_card(slide, x, Inches(5.6), Inches(third_w), Inches(1.0), CARD_BG, ACCENT_TEAL)
        add_text_box(slide, x + Inches(0.1), Inches(5.65), Inches(third_w - 0.2), Inches(0.3),
                     title, font_size=13, color=ACCENT_TEAL, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.1), Inches(5.95), Inches(third_w - 0.2), Inches(0.55),
                     desc, font_size=11, color=LIGHT_GREY, alignment=PP_ALIGN.CENTER)


def slide_kpis(prs):
    """Slide 6: Key Performance Indicators."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "KEY PERFORMANCE INDICATORS", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.4),
                 "Monitor these critical metrics every round. All affect your final Terminal Valuation.",
                 font_size=15, color=LIGHT_GREY)

    # Financial KPIs (left)
    add_text_box(slide, Inches(MARGIN), Inches(1.6), Inches(HALF_W), Inches(0.4),
                 "FINANCIAL", font_size=18, color=ACCENT_GOLD, bold=True)

    fin_kpis = [
        ("Treasury (CSF)", "Your capital pool for investments. Overspending triggers emergency credit."),
        ("EBITDA", "Earnings -- drives your terminal valuation. Protect revenue, control costs."),
        ("Revenue", "Per-unit income. Grows with investment, shrinks with crises."),
        ("Green Fund", "Earmarked sustainability budget. Unlocks special bidding in Round 3."),
    ]

    y = Inches(2.05)
    for name, desc in fin_kpis:
        add_text_box(slide, Inches(MARGIN + 0.2), y, Inches(HALF_W - 0.2), Inches(0.25),
                     f"  {name}", font_size=13, color=WHITE, bold=True)
        add_text_box(slide, Inches(MARGIN + 0.5), y + Inches(0.24), Inches(HALF_W - 0.5), Inches(0.3),
                     desc, font_size=11, color=LIGHT_GREY)
        y += Inches(0.58)

    # ESG KPIs (right)
    add_text_box(slide, Inches(RIGHT_X), Inches(1.6), Inches(HALF_W), Inches(0.4),
                 "SUSTAINABILITY", font_size=18, color=SUCCESS_GREEN, bold=True)

    esg_kpis = [
        ("Carbon (tCO2e)", "Total emissions. Carbon tax bites harder each year. Net-zero is the goal."),
        ("Reputation", "Stakeholder trust. Crisis contagion can crash it -- recovery is slow."),
        ("Social License", "Community goodwill. Below 30 triggers protests and revenue loss."),
        ("Natural Capital Debt", "Environmental debt that compounds. Ignore it and it spirals."),
    ]

    y = Inches(2.05)
    for name, desc in esg_kpis:
        add_text_box(slide, Inches(RIGHT_X + 0.2), y, Inches(HALF_W - 0.2), Inches(0.25),
                     f"  {name}", font_size=13, color=WHITE, bold=True)
        add_text_box(slide, Inches(RIGHT_X + 0.5), y + Inches(0.24), Inches(HALF_W - 0.5), Inches(0.3),
                     desc, font_size=11, color=LIGHT_GREY)
        y += Inches(0.58)

    # Operational section (left)
    add_text_box(slide, Inches(MARGIN), Inches(4.5), Inches(HALF_W), Inches(0.4),
                 "OPERATIONAL", font_size=18, color=RGBColor(0x33, 0x98, 0xDB), bold=True)

    op_kpis = [
        ("Synergy Multiplier", "Cross-BU collaboration savings. Grows with aligned investments."),
        ("Governance Risk", "Board and compliance exposure. High risk = cash conversion penalty."),
        ("Staff Burnout", "Above 20% triggers OPEX penalties. Above 70% is critical."),
    ]

    y = Inches(4.95)
    for name, desc in op_kpis:
        add_text_box(slide, Inches(MARGIN + 0.2), y, Inches(HALF_W - 0.2), Inches(0.25),
                     f"  {name}", font_size=13, color=WHITE, bold=True)
        add_text_box(slide, Inches(MARGIN + 0.5), y + Inches(0.24), Inches(HALF_W - 0.5), Inches(0.3),
                     desc, font_size=11, color=LIGHT_GREY)
        y += Inches(0.58)

    # Tip card (right bottom)
    add_rounded_card(slide, Inches(RIGHT_X), Inches(4.5), Inches(HALF_W), Inches(2.2),
                     CARD_BG, ACCENT_GOLD)
    add_text_box(slide, Inches(RIGHT_X + 0.2), Inches(4.6), Inches(HALF_W - 0.4), Inches(2.0),
                 "KEY INSIGHT\n\n"
                 "Financial and ESG metrics are deeply interconnected.\n"
                 "Ignoring carbon leads to tax penalties that destroy EBITDA.\n"
                 "Ignoring reputation triggers contagion cascades.\n"
                 "Balance is everything.",
                 font_size=13, color=LIGHT_GREY)


def slide_round_flow(prs):
    """Slide 7: How Each Round Works."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "HOW EACH ROUND WORKS", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    steps = [
        ("1", "READ THE BRIEFING",
         "Each round opens with a crisis scenario and Board directive.\n"
         "Understand what's at stake before making decisions.",
         ACCENT_TEAL),
        ("2", "CHECK YOUR MAILBOX",
         "Board members (CFO, CSO, Legal, CRO) send advice.\n"
         "Each has their own bias -- weigh their counsel carefully.",
         RGBColor(0x33, 0x98, 0xDB)),
        ("3", "CHOOSE YOUR STRATEGY",
         "Select Option A, B, or C. Each has different impacts\n"
         "on financial performance, ESG metrics, and stakeholder trust.",
         ACCENT_GOLD),
        ("4", "ALLOCATE CAPITAL",
         "Use the Investment Matrix to distribute your CSF pool\n"
         "across the four BUs. You can allocate up to 120% (credit).",
         RGBColor(0x9B, 0x59, 0xB6)),
        ("5", "COMMIT & SEE RESULTS",
         "Lock in your decisions. The engine calculates impacts.\n"
         "Review your KPI changes and prepare for the next round.",
         SUCCESS_GREEN),
    ]

    card_w = Inches(HALF_W)
    card_h = Inches(1.3)

    for i, (num, title, desc, accent) in enumerate(steps):
        col = i % 2
        row = i // 2
        x = Inches(MARGIN) if col == 0 else Inches(RIGHT_X)
        y = Inches(1.2) + row * Inches(1.6)

        add_rounded_card(slide, x, y, card_w, card_h, CARD_BG, accent)
        add_number_circle(slide, x + Inches(0.15), y + Inches(0.2), num, accent)
        add_text_box(slide, x + Inches(0.7), y + Inches(0.1), card_w - Inches(0.85), Inches(0.35),
                     title, font_size=15, color=accent, bold=True)
        add_text_box(slide, x + Inches(0.7), y + Inches(0.48), card_w - Inches(0.85), Inches(0.75),
                     desc, font_size=11, color=LIGHT_GREY)

    # Bottom flow arrow
    add_text_box(slide, Inches(MARGIN), Inches(6.2), Inches(CONTENT_W), Inches(0.4),
                 "Brief  -->  Decide  -->  Allocate  -->  Commit  -->  Results  -->  Next Round",
                 font_size=18, color=ACCENT_TEAL, bold=True, alignment=PP_ALIGN.CENTER)


def slide_investment_matrix(prs):
    """Slide 8: The Investment Matrix."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "THE INVESTMENT MATRIX", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    # Screenshot
    add_image_safe(slide, "investment_matrix.png", Inches(MARGIN), Inches(1.2),
                   width=Inches(CARD_FULL_W), height=Inches(2.8))

    # Explanation cards below
    cards = [
        ("CSF POOL", "Your total capital budget.\nStarts at $10M per round.\nGrows/shrinks with performance.", ACCENT_TEAL),
        ("120% CAP", "You can allocate up to 120%\nof your pool -- the excess is\nemergency credit at a cost.", ACCENT_GOLD),
        ("PER-UNIT METRICS", "Each BU shows OPEX base,\nmargin, social license, gov risk,\nand natural capital debt.", RGBColor(0x33, 0x98, 0xDB)),
    ]

    third_w = (CARD_FULL_W - 0.6) / 3
    for i, (title, desc, accent) in enumerate(cards):
        x = Inches(MARGIN + i * (third_w + 0.3))
        add_rounded_card(slide, x, Inches(4.3), Inches(third_w), Inches(2.2), CARD_BG, accent)
        add_text_box(slide, x + Inches(0.15), Inches(4.4), Inches(third_w - 0.3), Inches(0.35),
                     title, font_size=16, color=accent, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.15), Inches(4.85), Inches(third_w - 0.3), Inches(1.5),
                     desc, font_size=12, color=LIGHT_GREY, alignment=PP_ALIGN.CENTER)


def slide_roadmap(prs):
    """Slide 9: The 10-Round Journey."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "THE 10-ROUND JOURNEY", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    # Roadmap image (left)
    add_image_safe(slide, "roadmap.png", Inches(MARGIN), Inches(1.2),
                   width=Inches(HALF_W), height=Inches(5.0))

    # Round list on right
    rounds = [
        ("R1", "Foundations", "ESG Baseline"),
        ("R2", "Double Materiality", "Budget Allocation"),
        ("R3", "Scope 3 Emissions", "Supply Chain"),
        ("R4", "Contagion", "Reputation Crisis"),
        ("R5", "Climate", "Physical Risk"),
        ("R6", "AI Bias", "Algorithmic Ethics"),
        ("R7", "Circularity", "Circular Economy"),
        ("R8", "Blue Stress", "Water Scarcity"),
        ("R9", "Just Transition", "Workforce Justice"),
        ("R10", "Grand Finale", "Activist Ultimatum"),
    ]

    y = Inches(1.15)
    for rnd, name, theme in rounds:
        add_text_box(slide, Inches(RIGHT_X), y, Inches(0.6), Inches(0.3),
                     rnd, font_size=13, color=ACCENT_TEAL, bold=True)
        add_text_box(slide, Inches(RIGHT_X + 0.6), y, Inches(2.5), Inches(0.3),
                     name, font_size=14, color=WHITE, bold=True)
        add_text_box(slide, Inches(RIGHT_X + 3.3), y, Inches(2.5), Inches(0.3),
                     theme, font_size=12, color=LIGHT_GREY)
        y += Inches(0.48)

    # Phase labels
    phases = [
        ("YEAR 1-2  |  Foundation & Crisis", Inches(1.2), RGBColor(0x2E, 0xCC, 0x71)),
        ("YEAR 3-4  |  Resilience & Innovation", Inches(3.2), RGBColor(0x33, 0x98, 0xDB)),
        ("YEAR 5  |  Legacy & Valuation", Inches(5.2), ACCENT_GOLD),
    ]

    for text, py, color in phases:
        add_text_box(slide, Inches(RIGHT_X), py + Inches(4.8), Inches(HALF_W), Inches(0.3),
                     text, font_size=11, color=color, bold=True)


def slide_minigames(prs):
    """Slide 10: Minigames & Special Modules."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "MINIGAMES & SPECIAL MODULES", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.4),
                 "Specialist modules unlock automatically as you progress through rounds:",
                 font_size=15, color=LIGHT_GREY)

    modules = [
        ("Double Materiality Matrix", "R2", "Map ESG issues by impact + financial materiality (CSRD framework)"),
        ("Green Fund Bidding", "R3", "Bid on sustainability projects using MAC curve economics"),
        ("VCM Portfolio Builder", "R5", "Build a carbon credit portfolio across integrity tiers"),
        ("Policy War Room", "R8", "Game-theoretic regulatory lobbying simulation"),
        ("ESG Refinancing Simulator", "R9", "Model green bond pricing and brown penalty effects"),
        ("Circular Strategy Dashboard", "R10", "Design product-as-a-service models using ReSOLVE framework"),
        ("Boardroom Showdown", "Final", "High-stakes negotiation with an activist investor scenario"),
        ("AI Podcast", "Every Round", "Briefing by Dr. Priya Sharma & Prof. James Walker"),
    ]

    y = Inches(1.6)
    for i, (name, rnd, desc) in enumerate(modules):
        bg_color = CARD_BG if i % 2 == 0 else RGBColor(0x17, 0x25, 0x35)
        add_shape_rect(slide, Inches(MARGIN), y, Inches(CARD_FULL_W), Inches(0.55), bg_color)

        add_text_box(slide, Inches(MARGIN + 0.2), y + Inches(0.05), Inches(4.5), Inches(0.3),
                     name, font_size=14, color=WHITE, bold=True)
        add_text_box(slide, Inches(MARGIN + 5.0), y + Inches(0.08), Inches(1.2), Inches(0.3),
                     rnd, font_size=12, color=ACCENT_GOLD, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, Inches(MARGIN + 6.5), y + Inches(0.08), Inches(5.5), Inches(0.3),
                     desc, font_size=12, color=LIGHT_GREY)
        y += Inches(0.6)


def slide_terminal_valuation(prs):
    """Slide 11: Terminal Valuation."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "HOW YOU WIN: TERMINAL VALUATION", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    # TV formula image (left)
    add_image_safe(slide, "terminal_valuation.png", Inches(MARGIN), Inches(1.2),
                   width=Inches(HALF_W), height=Inches(5.2))

    # Explanation on right
    lines = [
        ("Your final score is your Terminal Valuation:", True, WHITE),
        ("", False, WHITE),
        ("TV  =  EBITDA  x  12  x  M_R", True, ACCENT_TEAL),
        ("", False, WHITE),
        ("Where:", True, LIGHT_GREY),
        ("", False, WHITE),
        ("  EBITDA = Revenue - OPEX - Carbon Tax", False, WHITE),
        ("  Your core profitability metric.", False, LIGHT_GREY),
        ("", False, WHITE),
        ("  Exit Multiple = 12x", False, WHITE),
        ("  Industry standard multiplier.", False, LIGHT_GREY),
        ("", False, WHITE),
        ("  M_R = Regenerative Multiple", False, WHITE),
        ("  Base 1.00 + bonuses for:", False, LIGHT_GREY),
        ("    Materiality     +0.10", False, SUCCESS_GREEN),
        ("    Synergy          +0.30", False, SUCCESS_GREEN),
        ("    Resilience       +0.20", False, SUCCESS_GREEN),
        ("    Truth              +0.15", False, SUCCESS_GREEN),
        ("    Community      +0.18", False, SUCCESS_GREEN),
        ("", False, WHITE),
        ("  Maximum M_R = 2.08", True, ACCENT_GOLD),
    ]
    add_multiline_text(slide, Inches(RIGHT_X), Inches(1.2), Inches(HALF_W), Inches(5.5),
                       lines, font_size=13, line_spacing=1.2)


def slide_archetypes(prs):
    """Slide 12: Corporate Archetypes."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "CORPORATE ARCHETYPES", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.4),
                 "Your M_R score determines your corporate archetype -- the story of how you led Muressons:",
                 font_size=15, color=LIGHT_GREY)

    # Archetypes image
    add_image_safe(slide, "archetypes.png", Inches(MARGIN), Inches(1.7),
                   width=Inches(CARD_FULL_W), height=Inches(5.0))


def slide_strategy_tips(prs):
    """Slide 13: Strategy Tips."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "STRATEGIC TIPS FOR SUCCESS", font_size=36, color=ACCENT_GOLD, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4), ACCENT_GOLD)

    tips = [
        ("Balance Profit & Planet",
         "Chasing short-term EBITDA while ignoring ESG will destroy your M_R multiplier. "
         "The winning strategy finds synergies between financial and sustainability goals."),
        ("Protect Your Revenue Engines",
         "Pharma and Electronics generate the most revenue. Neglecting their investment "
         "leads to margin compression and revenue decline."),
        ("Watch for Contagion",
         "Reputation crises in one BU spread to others via sigmoid contagion. "
         "Early containment is cheaper than late recovery."),
        ("Don't Over-Leverage",
         "The 120% credit facility is tempting but costly. The interest compounds. "
         "Smart allocation within 100% beats reckless overspending."),
        ("Read Your Board Advisors",
         "The CFO cares about margins. The CSO pushes sustainability. Legal warns about risk. "
         "The CRO focuses on stakeholders. Synthesise their advice -- don't follow one blindly."),
        ("Build Synergy Across BUs",
         "Aligned investments across business units unlock the synergy multiplier -- "
         "an OPEX reduction that compounds over rounds."),
    ]

    y = Inches(1.3)
    colors = [ACCENT_TEAL, RGBColor(0x33, 0x98, 0xDB), DANGER_RED,
              ACCENT_GOLD, RGBColor(0x9B, 0x59, 0xB6), SUCCESS_GREEN]
    for i, (title, desc) in enumerate(tips):
        accent = colors[i]
        add_rounded_card(slide, Inches(MARGIN), y, Inches(CARD_FULL_W), Inches(0.9), CARD_BG, accent)
        add_text_box(slide, Inches(MARGIN + 0.2), y + Inches(0.05), Inches(CARD_FULL_W - 0.4), Inches(0.3),
                     title, font_size=15, color=accent, bold=True)
        add_text_box(slide, Inches(MARGIN + 0.2), y + Inches(0.38), Inches(CARD_FULL_W - 0.4), Inches(0.45),
                     desc, font_size=11, color=LIGHT_GREY)
        y += Inches(0.97)


def slide_strategic_pillars(prs):
    """Slide 14: Strategic Pillars."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "STRATEGIC PILLARS", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.5),
                 "Each round, you make independent decisions across 5 strategic areas."
                 " Each area offers 3 options with different cost/impact trade-offs:",
                 font_size=15, color=LIGHT_GREY)

    pillars = [
        ("ENERGY", "Power Purchase Agreements, solar CapEx,\nfleet electrification, green data centres",
         "Carbon Intensity, Reputation",
         RGBColor(0xF3, 0x9C, 0x12)),
        ("OPERATIONS", "Lean processes, digital twins,\nAI governance, closed-loop manufacturing",
         "Governance Risk, Reputation, OPEX",
         RGBColor(0x33, 0x98, 0xDB)),
        ("SUPPLY CHAIN", "Supplier audits, blockchain traceability,\ngeographic diversification, nearshoring",
         "Social License, Reputation, Supply Risk",
         RGBColor(0x2E, 0xCC, 0x71)),
        ("OFFSETTING", "Nature-based offsets, carbon credits,\ncommunity funds, climate adaptation",
         "Natural Capital Debt, Social License",
         RGBColor(0x9B, 0x59, 0xB6)),
        ("HUMAN RESOURCES", "DEI programmes, leadership dev,\ngreen skills academy, crisis support",
         "Social License, Burnout, Workforce Readiness",
         RGBColor(0xE8, 0x4D, 0x4D)),
    ]

    icons = ["E", "O", "S", "C", "H"]
    y = Inches(1.7)
    for i, (name, examples, impacts, accent) in enumerate(pillars):
        bg_color = CARD_BG if i % 2 == 0 else RGBColor(0x17, 0x25, 0x35)
        add_rounded_card(slide, Inches(MARGIN), y, Inches(CARD_FULL_W), Inches(0.95), bg_color, accent)

        # Icon circle
        circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(MARGIN + 0.2), y + Inches(0.18),
                                        Inches(0.5), Inches(0.5))
        circle.fill.solid()
        circle.fill.fore_color.rgb = accent
        circle.line.fill.background()
        tf = circle.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = icons[i]
        run.font.size = Pt(18)
        run.font.bold = True
        run.font.color.rgb = DARK_BG

        add_text_box(slide, Inches(MARGIN + 0.9), y + Inches(0.08), Inches(3.0), Inches(0.3),
                     name, font_size=16, color=accent, bold=True)
        add_text_box(slide, Inches(MARGIN + 0.9), y + Inches(0.4), Inches(4.0), Inches(0.5),
                     examples, font_size=10, color=LIGHT_GREY)
        add_text_box(slide, Inches(MARGIN + 6.5), y + Inches(0.15), Inches(1.2), Inches(0.3),
                     "Impacts:", font_size=11, color=MID_GREY, bold=True)
        add_text_box(slide, Inches(MARGIN + 7.8), y + Inches(0.15), Inches(4.0), Inches(0.7),
                     impacts, font_size=11, color=WHITE)
        y += Inches(1.02)

    add_text_box(slide, Inches(MARGIN), Inches(6.85), Inches(CONTENT_W), Inches(0.3),
                 "Each pillar choice costs treasury and sets flags that affect future rounds.",
                 font_size=12, color=MID_GREY, alignment=PP_ALIGN.CENTER)


def slide_alternate_pathways(prs):
    """Slide 15: Alternate Ending Pathways overview."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "ALTERNATE ENDING PATHWAYS", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.5),
                 "Round 10 is not always the same! Your facilitator selects an ending pathway "
                 "that shapes the final crisis. Foreshadowing clues appear from Round 5 onwards:",
                 font_size=15, color=LIGHT_GREY)

    pathways = [
        ("Activist Ultimatum", "An activist consortium acquires a blocking stake "
         "and forces a strategic review: integrate, spin-off, or divest.",
         "DEFAULT", ACCENT_TEAL),
        ("Climate Black Swan", "Cascading climate catastrophe triggers stranded "
         "asset write-downs. Carbon tax triples. Can you decarbonise in time?",
         "CI-FOCUSED", RGBColor(0xE8, 0x4D, 0x4D)),
        ("Stakeholder Revolt", "Employees strike, communities protest, consumers "
         "boycott. Triple stakeholder ultimatum demands a social compact.",
         "SLO-FOCUSED", RGBColor(0x9B, 0x59, 0xB6)),
        ("Hostile Takeover", "A PE firm launches a hostile bid. Weak governance "
         "and low synergy make you vulnerable. Defend or accept?",
         "SYNERGY-FOCUSED", RGBColor(0xF3, 0x9C, 0x12)),
        ("Regulatory Shutdown", "A whistleblower triggers a CSDDD investigation. "
         "The regulator threatens operational shutdown. Remediate or fight?",
         "GOVERNANCE-FOCUSED", RGBColor(0x33, 0x98, 0xDB)),
    ]

    y = Inches(1.75)
    for i, (name, desc, tag, accent) in enumerate(pathways):
        bg = CARD_BG if i % 2 == 0 else RGBColor(0x17, 0x25, 0x35)
        add_rounded_card(slide, Inches(MARGIN), y, Inches(CARD_FULL_W), Inches(0.9), bg, accent)

        add_text_box(slide, Inches(MARGIN + 0.3), y + Inches(0.08), Inches(4.5), Inches(0.3),
                     name, font_size=16, color=accent, bold=True)
        add_text_box(slide, Inches(MARGIN + 0.3), y + Inches(0.38), Inches(8.0), Inches(0.45),
                     desc, font_size=12, color=LIGHT_GREY)
        add_text_box(slide, Inches(SLIDE_W - 2.8), y + Inches(0.3), Inches(2.0), Inches(0.3),
                     tag, font_size=10, color=accent, bold=True, alignment=PP_ALIGN.CENTER)
        y += Inches(0.97)

    add_rounded_card(slide, Inches(MARGIN), Inches(6.7), Inches(CARD_FULL_W), Inches(0.5),
                     CARD_BG, ACCENT_GOLD)
    add_text_box(slide, Inches(MARGIN + 0.3), Inches(6.75), Inches(CARD_FULL_W - 0.6), Inches(0.4),
                 "Watch for foreshadowing events in Rounds 5-8 -- they hint at which pathway is active!",
                 font_size=12, color=ACCENT_GOLD)


# -- Pathway detail slides (shared helper) --

def _pathway_detail_slide(prs, name, crisis_title, crisis_icon, crisis_desc,
                          options, mr_bonuses, mr_penalties, archetype_override,
                          accent, foreshadow_hint):
    """Helper: build a single detailed pathway slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 f"PATHWAY: {name.upper()}", font_size=32, color=accent, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.85), Inches(4), accent)

    # Crisis box
    add_rounded_card(slide, Inches(MARGIN), Inches(1.05), Inches(CARD_FULL_W), Inches(1.1),
                     CARD_BG, accent)
    add_text_box(slide, Inches(MARGIN + 0.3), Inches(1.1), Inches(CARD_FULL_W - 0.6), Inches(0.3),
                 f"{crisis_icon}  {crisis_title}", font_size=18, color=accent, bold=True)
    add_text_box(slide, Inches(MARGIN + 0.3), Inches(1.45), Inches(CARD_FULL_W - 0.6), Inches(0.6),
                 crisis_desc, font_size=12, color=LIGHT_GREY)

    # Three options
    add_text_box(slide, Inches(MARGIN), Inches(2.3), Inches(CONTENT_W), Inches(0.3),
                 "R10 STRATEGIC OPTIONS", font_size=15, color=ACCENT_GOLD, bold=True)

    opt_colors = [SUCCESS_GREEN, RGBColor(0x33, 0x98, 0xDB), DANGER_RED]
    y = Inches(2.65)
    for i, (label, title, desc) in enumerate(options):
        c = opt_colors[i]
        add_rounded_card(slide, Inches(MARGIN), y, Inches(CARD_FULL_W), Inches(0.75), CARD_BG, c)
        add_text_box(slide, Inches(MARGIN + 0.2), y + Inches(0.05), Inches(0.4), Inches(0.25),
                     label, font_size=16, color=c, bold=True)
        add_text_box(slide, Inches(MARGIN + 0.7), y + Inches(0.05), Inches(3.5), Inches(0.25),
                     title, font_size=14, color=c, bold=True)
        add_text_box(slide, Inches(MARGIN + 0.7), y + Inches(0.32), Inches(CARD_FULL_W - 1.2), Inches(0.4),
                     desc, font_size=10, color=LIGHT_GREY)
        y += Inches(0.82)

    # M_R Bonuses & Penalties (two columns)
    add_text_box(slide, Inches(MARGIN), Inches(5.2), Inches(HALF_W), Inches(0.25),
                 "M_R BONUSES", font_size=13, color=SUCCESS_GREEN, bold=True)
    by = Inches(5.45)
    for bonus in mr_bonuses:
        add_text_box(slide, Inches(MARGIN + 0.2), by, Inches(HALF_W - 0.2), Inches(0.22),
                     bonus, font_size=10, color=SUCCESS_GREEN)
        by += Inches(0.22)

    add_text_box(slide, Inches(RIGHT_X), Inches(5.2), Inches(HALF_W), Inches(0.25),
                 "M_R PENALTIES", font_size=13, color=DANGER_RED, bold=True)
    py = Inches(5.45)
    for penalty in mr_penalties:
        add_text_box(slide, Inches(RIGHT_X + 0.2), py, Inches(HALF_W - 0.2), Inches(0.22),
                     penalty, font_size=10, color=DANGER_RED)
        py += Inches(0.22)

    # Foreshadowing hint
    add_rounded_card(slide, Inches(MARGIN), Inches(6.6), Inches(CARD_FULL_W), Inches(0.5),
                     CARD_BG, MID_GREY)
    add_text_box(slide, Inches(MARGIN + 0.3), Inches(6.65), Inches(CARD_FULL_W - 0.6), Inches(0.4),
                 f"FORESHADOWING (R5-R8): {foreshadow_hint}",
                 font_size=11, color=MID_GREY)


def slide_pathway_activist(prs):
    _pathway_detail_slide(prs,
        name="Activist Ultimatum",
        crisis_title="The Board Under Siege",
        crisis_icon="[!]",
        crisis_desc=(
            "An activist consortium has acquired a blocking stake in Muressons Group. "
            "They demand a strategic review -- integration, spin-off, or full divestiture. "
            "The board must choose how to respond while protecting shareholder value "
            "and the company's long-term sustainability trajectory."),
        options=[
            ("A", "Strategic Integration",
             "Integrate activist demands into long-term strategy. High cost but preserves unity. "
             "M_R bonuses for synergy and materiality alignment."),
            ("B", "Partial Spin-Off",
             "Spin off underperforming BUs to satisfy activist. Moderate cost. "
             "Preserves core but reduces portfolio diversification."),
            ("C", "Full Divestiture",
             "Accept breakup. Short-term cash gain but destroys synergy. "
             "Exit multiple drops to 8x. M_R capped at 1.0."),
        ],
        mr_bonuses=[
            "+0.10  Materiality alignment (CSRD governance in R2)",
            "+0.30  Synergy bonus (Synergy Score >= 80)",
            "+0.20  Resilience bonus (survived R5/R8 crises)",
            "+0.15  Truth premium (ethical AI overhaul in R6)",
            "+0.18  Community champion (community fund in R9)",
        ],
        mr_penalties=[
            "-0.40  Instability discount (avg SLO < 75)",
            "-0.20  Shadow Board rejection penalty",
        ],
        archetype_override="Regenerative Titan / De-risked Safe Haven / Fragile Giant / Stranded Relic",
        accent=ACCENT_TEAL,
        foreshadow_hint="R6: Activist files 13D (4.9% stake) | R7: Analyst restructuring note | R8: Blocking stake reached",
    )


def slide_pathway_climate(prs):
    _pathway_detail_slide(prs,
        name="Climate Black Swan",
        crisis_title="The Stranded Asset Reckoning",
        crisis_icon="[!!]",
        crisis_desc=(
            "The world has entered a climate emergency. Carbon pricing has tripled. "
            "Insurance markets refuse to underwrite high-exposure assets. A cascading "
            "climate catastrophe demands an immediate strategic response. "
            "Your carbon intensity history determines your fate."),
        options=[
            ("A", "Emergency Decarbonisation",
             "Halve all BU carbon intensities. NCD reduced 50%. Treasury -$20M. "
             "If avg CI < 25: +0.30 M_R Climate Leader bonus."),
            ("B", "Climate Adaptation Portfolio",
             "Divest BUs with CI > 40 at fire-sale prices (50% book value). "
             "Remaining BUs receive reallocation capital."),
            ("C", "Deny & Delay",
             "Lobby against carbon regulation. Carbon tax triples, NCD doubles. "
             "Exit multiple drops to 6x. M_R penalty -0.40."),
        ],
        mr_bonuses=[
            "+0.30  Climate Leader (avg CI < 25 at R10)",
            "+0.20  Adaptation Premium (nature-based + early decarboniser)",
            "+0.15  Carbon Transition (CI reduced >= 40% from R1)",
        ],
        mr_penalties=[
            "-0.40  Stranded Asset Penalty (avg CI > 50 at R10)",
            "-0.20  Shadow Board planet rejection penalty",
            "Exit multiple haircut based on avg CI",
        ],
        archetype_override="Climate Pioneer / Adapted Enterprise / Stranded Giant / Fossil Relic",
        accent=RGBColor(0xE8, 0x4D, 0x4D),
        foreshadow_hint="R5: IPCC 1.5C overshoot | R6: Carbon futures +40% | R7: Uninsurable assets warning | R8: 1.5C breached",
    )


def slide_pathway_stakeholder(prs):
    _pathway_detail_slide(prs,
        name="Stakeholder Revolt",
        crisis_title="The Social Reckoning",
        crisis_icon="[!!!]",
        crisis_desc=(
            "Employees, communities, and consumers have issued simultaneous ultimatums. "
            "Unionised workers demand burnout protections. Local councils threaten to revoke "
            "operating licences. A consumer boycott is reducing revenue. "
            "The board must respond to the triple stakeholder revolt."),
        options=[
            ("A", "Total Stakeholder Compact",
             "Legally binding charter: living wages, community agreements, quality standards. "
             "Treasury -$18M. Revenue +15%. If SLO >= 70 AND burnout < 30: +0.35 M_R."),
            ("B", "Selective Appeasement",
             "Address the loudest group only (auto-selects worst metric). Treasury -$8M. "
             "Fixes one dimension, unaddressed groups escalate (-10 SLO)."),
            ("C", "Corporate Hardball",
             "Threaten overseas relocation. All SLO -25, burnout +20. Treasury +$10M. "
             "If any BU SLO hits 0, that BU is shuttered. M_R penalty -0.30."),
        ],
        mr_bonuses=[
            "+0.35  Social Regeneration (SLO >= 70 AND burnout < 30)",
            "+0.15  Employee Champion (burnout < 25 AND readiness >= 70)",
            "+0.15  Community Trust (avg SLO >= 80)",
        ],
        mr_penalties=[
            "-0.50  Social Collapse (avg SLO < 40 OR burnout > 70)",
            "-0.20  Shadow Board shareholder alienation",
        ],
        archetype_override="People's Corporation / Responsible Employer / Contested Enterprise / Social Pariah",
        accent=RGBColor(0x9B, 0x59, 0xB6),
        foreshadow_hint="R5: Toxic culture review | R6: Community coalition | R7: #BoycottMuressons trends | R8: Triple ultimatum",
    )


def slide_pathway_takeover(prs):
    _pathway_detail_slide(prs,
        name="Hostile Takeover",
        crisis_title="The Corporate Raider",
        crisis_icon="[!]",
        crisis_desc=(
            "Cerberus Capital has launched a hostile tender offer at a 15% premium. "
            "The PE firm plans to break up the conglomerate and sell individual BUs. "
            "The board has 48 hours to respond. Your synergy multiplier and treasury "
            "strength determine whether shareholders side with management or the raider."),
        options=[
            ("A", "White Knight Defence",
             "Seek a friendly acquirer who preserves the integrated strategy. Treasury -$15M. "
             "If synergy >= 1.3 AND treasury > $30M: +0.25 M_R. Revenue -5% friction."),
            ("B", "Poison Pill + Crown Jewel Lock-Up",
             "Dilutive share issuance and lock-up agreements. Treasury -$25M. "
             "Preserves independence but exit multiple drops to 10x (debt overhang)."),
            ("C", "Accept the Bid",
             "Take the premium. Treasury +$20M but conglomerate broken up. "
             "Exit multiple locked at 8x. M_R capped at 1.0, penalty -0.50."),
        ],
        mr_bonuses=[
            "+0.25  Strategic Integration (synergy >= 1.3 AND treasury > $30M)",
            "+0.20  Fortress Premium (EBITDA margin > 20% AND no scandals)",
            "+0.15  Conglomerate Premium (synergy >= 1.5)",
        ],
        mr_penalties=[
            "-0.40  Vulnerable Target (synergy < 1.1 AND treasury < $10M)",
            "-0.20  Shadow Board shareholder alienation",
        ],
        archetype_override="Untouchable Fortress / Defended Platform / Vulnerable Target / Broken Conglomerate",
        accent=RGBColor(0xF3, 0x9C, 0x12),
        foreshadow_hint="R6: Unusual share volume | R7: PE firm 'denies' interest | R8: Preliminary offer filed with regulator",
    )


def slide_pathway_regulatory(prs):
    _pathway_detail_slide(prs,
        name="Regulatory Shutdown",
        crisis_title="The Compliance Reckoning",
        crisis_icon="[!]",
        crisis_desc=(
            "The environmental regulator has completed its investigation triggered by a whistleblower. "
            "Muressons faces a Notice of Violation under the CSDDD, citing systematic failures "
            "in supply chain due diligence. The regulator can impose operational restrictions, "
            "heavy fines, or a consent decree requiring third-party monitoring."),
        options=[
            ("A", "Full Remediation Programme",
             "Exceed CSDDD requirements: full traceability, impact assessments, remediation fund. "
             "Cost $4M per BU. If ethical score > 7 AND no scandals: +0.30 M_R."),
            ("B", "Negotiate Consent Decree",
             "Accept $30M fine and 3-year third-party monitoring. Operations continue. "
             "Exit multiple reduced to 10x. Carbon tax increases to $350/t."),
            ("C", "Contest the Ruling",
             "Challenge in court. Legal costs $10M. If unsuccessful (likely if ethical score < 5): "
             "double fine ($60M), worst BU suspended, exit multiple to 7x, reputation -30."),
        ],
        mr_bonuses=[
            "+0.30  Regulatory Exemplar (ethical score > 7, no scandals)",
            "+0.20  Supply Chain Transparency (scope 3 or full remediation)",
            "+0.15  Proactive Compliance (ethical score > 6 AND SLO > 60)",
        ],
        mr_penalties=[
            "-0.45  Regulatory Failure (ethical score < 4)",
            "-0.25  Shadow Board governance fragility",
            "-0.35  Contest ruling M_R penalty (if unsuccessful)",
        ],
        archetype_override="Compliance Champion / Regulated Enterprise / Monitored Entity / Suspended Operation",
        accent=RGBColor(0x33, 0x98, 0xDB),
        foreshadow_hint="R5: CSDDD adopted | R6: Peers face $50M+ compliance | R7: Whistleblower contacts regulator | R8: Show cause notice",
    )


def slide_sankey_diagram(prs):
    """Slide 21: Consequence DNA Sankey Diagram."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "CONSEQUENCE DNA VISUALIZER", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.5),
                 "The Sankey diagram maps the causal chain from your decisions to their terminal "
                 "value impact. It activates after the Round 5 Shadow Board Audit:",
                 font_size=15, color=LIGHT_GREY)

    # 5-column flow diagram
    cols = [
        ("DECISIONS", "Your R1-R10 choices.\nEach coded by Leverage\nPoint depth (LP1-LP12).\nDeeper = more systemic.",
         ACCENT_TEAL),
        ("CAUSAL FLAGS", "Flags set by decisions\nthat persist across rounds.\ne.g. renewable_ppa_signed,\nsbti_committed.",
         SUCCESS_GREEN),
        ("SYSTEM AGENTS", "AI stakeholder agents\nthat constrict value flow.\nStages: dormant, watching,\nagitated, hostile, triggered.",
         RGBColor(0xF3, 0x9C, 0x12)),
        ("METRIC SHIFTS", "Concrete KPI changes\ncaused by flag activation.\ne.g. carbon -8, reputation\n+5, SLO +3.",
         RGBColor(0x33, 0x98, 0xDB)),
        ("M_R PROJECTION", "Final M_R contribution\nof each causal chain.\nPositive (green) or\nnegative (red) delta.",
         RGBColor(0x9B, 0x59, 0xB6)),
    ]

    col_count = len(cols)
    gap = 0.2
    col_w = (CARD_FULL_W - gap * (col_count - 1)) / col_count
    for i, (title, desc, accent_c) in enumerate(cols):
        x = Inches(MARGIN + i * (col_w + gap))
        add_rounded_card(slide, x, Inches(1.75), Inches(col_w), Inches(2.3), CARD_BG, accent_c)
        add_text_box(slide, x + Inches(0.1), Inches(1.8), Inches(col_w - 0.2), Inches(0.3),
                     title, font_size=11, color=accent_c, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.1), Inches(2.2), Inches(col_w - 0.2), Inches(1.6),
                     desc, font_size=10, color=LIGHT_GREY, alignment=PP_ALIGN.CENTER)

    # Flow arrows between columns
    for i in range(col_count - 1):
        arrow_x = Inches(MARGIN + (i + 1) * (col_w + gap) - gap / 2)
        add_text_box(slide, arrow_x, Inches(2.7), Inches(gap), Inches(0.3),
                     ">", font_size=18, color=MID_GREY, alignment=PP_ALIGN.CENTER)

    # Key concepts below
    add_text_box(slide, Inches(MARGIN), Inches(4.25), Inches(CONTENT_W), Inches(0.3),
                 "KEY CONCEPTS", font_size=16, color=ACCENT_GOLD, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(4.6), Inches(3), ACCENT_GOLD)

    concepts = [
        ("Leverage Points (LP1-LP12)",
         "Based on Donella Meadows' framework. LP1 (paradigm shift) = deepest intervention. "
         "LP12 (parameter tweak) = shallowest. Deeper decisions create more systemic change.",
         ACCENT_TEAL),
        ("Constriction Agents",
         "AI stakeholder agents that model real-world pressure groups. When triggered, "
         "they constrict value flow between metrics and M_R, reducing your terminal valuation.",
         RGBColor(0xF3, 0x9C, 0x12)),
        ("Red DNA Nodes",
         "Option C consequences that create permanent structural damage. These appear as "
         "red warning markers -- constrictions and value leaks that cannot be reversed.",
         DANGER_RED),
    ]

    y = Inches(4.75)
    for title, desc, accent_c in concepts:
        add_rounded_card(slide, Inches(MARGIN), y, Inches(CARD_FULL_W), Inches(0.62), CARD_BG, accent_c)
        add_text_box(slide, Inches(MARGIN + 0.3), y + Inches(0.05), Inches(3.5), Inches(0.25),
                     title, font_size=13, color=accent_c, bold=True)
        add_text_box(slide, Inches(MARGIN + 4.0), y + Inches(0.05), Inches(CARD_FULL_W - 4.5), Inches(0.5),
                     desc, font_size=10, color=LIGHT_GREY)
        y += Inches(0.68)

    add_text_box(slide, Inches(MARGIN), Inches(6.85), Inches(CONTENT_W), Inches(0.3),
                 "The DNA Visualizer activates after R5 and is available as a frozen snapshot in the final scorecard.",
                 font_size=11, color=MID_GREY, alignment=PP_ALIGN.CENTER)


def slide_endgame(prs):
    """Slide 22: The Endgame."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "THE ENDGAME", font_size=36, color=ACCENT_GOLD, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4), ACCENT_GOLD)

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.4),
                 "After Round 10, the simulation enters the endgame sequence:",
                 font_size=15, color=LIGHT_GREY)

    stages = [
        ("1", "TERMINAL VALUATION",
         "The engine calculates your final TV = EBITDA x 12 x M_R.\n"
         "All bonuses and penalties from 10 rounds are tallied.",
         ACCENT_TEAL),
        ("2", "BALANCED SCORECARD",
         "A 4-perspective analysis of your performance:\n"
         "Financial, Stakeholder, Internal Processes, Learning & Growth.",
         RGBColor(0x33, 0x98, 0xDB)),
        ("3", "ARCHETYPE REVEAL",
         "Your corporate archetype is revealed based on M_R score:\n"
         "Regenerative Titan, De-risked Safe Haven, Fragile Giant, or Stranded Relic.",
         RGBColor(0x9B, 0x59, 0xB6)),
        ("4", "BOARDROOM SHOWDOWN",
         "A high-stakes negotiation scenario where you face an activist\n"
         "investor (or pathway-specific antagonist) in a final confrontation.",
         ACCENT_GOLD),
        ("5", "CEO INTERVIEW",
         "An AI-powered CEO interviews you on your strategic decisions.\n"
         "Your responses are scored on 6 competency dimensions.",
         RGBColor(0xE8, 0x4D, 0x4D)),
        ("6", "LEADERBOARD & REPORT",
         "Final rankings against other players. Download your\n"
         "comprehensive HTML report with all metrics and analysis.",
         SUCCESS_GREEN),
    ]

    for i, (num, title, desc, accent) in enumerate(stages):
        col = i % 2
        row = i // 2
        x = Inches(MARGIN) if col == 0 else Inches(RIGHT_X)
        y = Inches(1.6) + row * Inches(1.7)

        add_rounded_card(slide, x, y, Inches(HALF_W), Inches(1.45), CARD_BG, accent)
        add_number_circle(slide, x + Inches(0.15), y + Inches(0.2), num, accent)
        add_text_box(slide, x + Inches(0.7), y + Inches(0.1), Inches(HALF_W - 0.85), Inches(0.3),
                     title, font_size=15, color=accent, bold=True)
        add_text_box(slide, x + Inches(0.7), y + Inches(0.48), Inches(HALF_W - 0.85), Inches(0.9),
                     desc, font_size=11, color=LIGHT_GREY)

    add_text_box(slide, Inches(MARGIN), Inches(6.85), Inches(CONTENT_W), Inches(0.4),
                 "R10  >>  Valuation  >>  Scorecard  >>  Showdown  >>  Interview  >>  Report",
                 font_size=16, color=ACCENT_GOLD, bold=True, alignment=PP_ALIGN.CENTER)


def slide_balanced_scorecard(prs):
    """Slide 23: The Sustainability Balanced Scorecard."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "BALANCED SCORECARD", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    # Screenshot (left)
    add_image_safe(slide, "scorecard.png", Inches(MARGIN), Inches(1.2),
                   width=Inches(HALF_W), height=Inches(3.5))

    # 4 perspectives on the right
    perspectives = [
        ("FINANCIAL", "Adjusted EBITDA (after carbon tax)\nGreen Cost of Debt (NRRS)",
         RGBColor(0x33, 0x98, 0xDB)),
        ("STAKEHOLDER", "Group Reputation (0-100)\nSocial License to Operate",
         RGBColor(0x2E, 0xCC, 0x71)),
        ("INTERNAL", "Industrial Synergy multiplier\nCarbon Liability (tonnes)",
         RGBColor(0xF3, 0x9C, 0x12)),
        ("LEARNING", "Talent Retention Index\nJust Transition & VRIO status",
         RGBColor(0x9B, 0x59, 0xB6)),
    ]

    y = Inches(1.2)
    for name, metrics, accent in perspectives:
        add_rounded_card(slide, Inches(RIGHT_X), y, Inches(HALF_W), Inches(0.82), CARD_BG, accent)
        add_text_box(slide, Inches(RIGHT_X + 0.2), y + Inches(0.05), Inches(2.0), Inches(0.25),
                     name, font_size=13, color=accent, bold=True)
        add_text_box(slide, Inches(RIGHT_X + 2.3), y + Inches(0.05), Inches(HALF_W - 2.7), Inches(0.7),
                     metrics, font_size=10, color=LIGHT_GREY)
        y += Inches(0.88)

    # Features section below
    add_text_box(slide, Inches(MARGIN), Inches(4.9), Inches(CONTENT_W), Inches(0.3),
                 "SCORECARD FEATURES", font_size=16, color=ACCENT_GOLD, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(5.25), Inches(3), ACCENT_GOLD)

    features = [
        ("M_R Breakdown", "See exactly how each bonus/penalty contributed to your Regenerative Multiple"),
        ("Critical Analysis", "AI-generated strengths, weaknesses, and missed opportunities"),
        ("TBL Matrix", "Triple Bottom Line view: People, Planet, Profit across all BUs"),
        ("Performance Trends", "Round-by-round charts: EBITDA, carbon, reputation, treasury, synergy"),
        ("Downloadable Report", "Export a comprehensive HTML report of your entire simulation performance"),
    ]

    y = Inches(5.45)
    for name, desc in features:
        add_text_box(slide, Inches(MARGIN + 0.2), y, Inches(3.0), Inches(0.25),
                     name, font_size=12, color=WHITE, bold=True)
        add_text_box(slide, Inches(MARGIN + 3.5), y, Inches(CONTENT_W - 4.0), Inches(0.25),
                     desc, font_size=11, color=LIGHT_GREY)
        y += Inches(0.32)


def slide_ceo_interview(prs):
    """Slide 24: The CEO Interview."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "CEO INTERVIEW", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.5),
                 "After Round 10, the CEO of Muressons interviews you on your strategic decisions. "
                 "An AI voice asks 5 questions and scores your responses across 6 competency dimensions:",
                 font_size=15, color=LIGHT_GREY)

    # 6 Dimensions (left)
    dimensions = [
        ("Strategic Thinking", "Long-term vs short-term trade-off awareness"),
        ("Stakeholder Empathy", "Articulating competing stakeholder interests"),
        ("Financial Acumen", "Understanding of treasury, EBITDA, M_R mechanics"),
        ("Ethical Reasoning", "Moral framework sophistication"),
        ("Systems Thinking", "Understanding cross-round flag dependencies"),
        ("Adaptive Leadership", "Willingness to change strategy with new info"),
    ]

    add_text_box(slide, Inches(MARGIN), Inches(1.7), Inches(HALF_W), Inches(0.3),
                 "6 COMPETENCY DIMENSIONS", font_size=16, color=ACCENT_GOLD, bold=True)

    colors = [ACCENT_TEAL, SUCCESS_GREEN, RGBColor(0x33, 0x98, 0xDB),
              RGBColor(0x9B, 0x59, 0xB6), RGBColor(0xF3, 0x9C, 0x12), DANGER_RED]

    y = Inches(2.1)
    for i, (name, desc) in enumerate(dimensions):
        add_rounded_card(slide, Inches(MARGIN), y, Inches(HALF_W), Inches(0.58), CARD_BG, colors[i])
        add_text_box(slide, Inches(MARGIN + 0.2), y + Inches(0.05), Inches(2.5), Inches(0.25),
                     name, font_size=12, color=colors[i], bold=True)
        add_text_box(slide, Inches(MARGIN + 2.8), y + Inches(0.08), Inches(HALF_W - 3.2), Inches(0.4),
                     desc, font_size=10, color=LIGHT_GREY)
        y += Inches(0.63)

    # How it works (right)
    add_text_box(slide, Inches(RIGHT_X), Inches(1.7), Inches(HALF_W), Inches(0.3),
                 "HOW IT WORKS", font_size=16, color=ACCENT_GOLD, bold=True)

    how_items = [
        ("4 Core Questions", "Asked every session -- covering strategy,\n"
         "trade-offs, systems effects, and hindsight."),
        ("1 Pathway Question", "Tailored to your ending pathway --\n"
         "tests domain-specific strategic insight."),
        ("50/50 Scoring", "Final score blends simulation performance\n"
         "data (50%) with interview response quality (50%)."),
        ("Spider Diagram", "Your results are visualised as a radar\n"
         "chart showing strengths and growth areas."),
    ]

    y = Inches(2.1)
    for title, desc in how_items:
        add_rounded_card(slide, Inches(RIGHT_X), y, Inches(HALF_W), Inches(0.95), CARD_BG, ACCENT_TEAL)
        add_text_box(slide, Inches(RIGHT_X + 0.2), y + Inches(0.05), Inches(HALF_W - 0.4), Inches(0.25),
                     title, font_size=13, color=ACCENT_TEAL, bold=True)
        add_text_box(slide, Inches(RIGHT_X + 0.2), y + Inches(0.32), Inches(HALF_W - 0.4), Inches(0.55),
                     desc, font_size=10, color=LIGHT_GREY)
        y += Inches(1.0)

    # Bottom note
    add_rounded_card(slide, Inches(MARGIN), Inches(6.3), Inches(CARD_FULL_W), Inches(0.7),
                     CARD_BG, RGBColor(0x9B, 0x59, 0xB6))
    add_text_box(slide, Inches(MARGIN + 0.3), Inches(6.38), Inches(CARD_FULL_W - 0.6), Inches(0.55),
                 "The CEO interview is an optional post-game module. Your facilitator will tell you "
                 "if it's enabled. Prepare by reflecting on your key decisions and their outcomes.",
                 font_size=12, color=LIGHT_GREY)


def slide_stakeholder_matrix(prs):
    """Slide: Autonomous Stakeholder Analysis Matrix."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "STAKEHOLDER ANALYSIS MATRIX", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.5),
                 "5 AI-driven stakeholder agents monitor your KPIs every round. Each has tolerance levels, "
                 "grievance memory, and cascading triggers based on Mitchell et al. (1997) Stakeholder Salience:",
                 font_size=14, color=LIGHT_GREY)

    agents = [
        ("Commissioner Carson", "The Regulator", "EU DG FISMA",
         "Gov Risk > 55  |  Reputation < 35  |  Carbon > 70",
         "Regulatory Shutdown Order", RGBColor(0x63, 0x66, 0xF1)),
        ("Greta Berg", "Gen Z Employee", "Workers United",
         "Burnout > 55  |  Reputation < 40  |  Gov Risk > 50",
         "Coordinated Strike Action", RGBColor(0xEC, 0x48, 0x99)),
        ("Marcus Chen-Hoffmann", "Institutional Investor", "Nordic Pension Alliance",
         "Treasury < 0  |  Reputation < 40  |  Carbon > 65",
         "Institutional Divestment Fire Sale", RGBColor(0xF5, 0x9E, 0x0B)),
        ("Megha Patrike", "Community Activist", "Deccan Plateau Council",
         "SLO < 45  |  Water Stress > 0.5  |  NCD > 200K",
         "Community Blockade & Injunction", RGBColor(0x10, 0xB9, 0x81)),
        ("Jay Buffet", "Investigative Journalist", "Deccan Herald",
         "Reputation < 42  |  Gov Risk > 48  |  Carbon > 60",
         "Viral Expose", RGBColor(0x8B, 0x5C, 0xF6)),
    ]

    y = Inches(1.7)
    for name, role, org, red_lines, trigger_event, accent in agents:
        add_rounded_card(slide, Inches(MARGIN), y, Inches(CARD_FULL_W), Inches(0.88), CARD_BG, accent)
        add_text_box(slide, Inches(MARGIN + 0.2), y + Inches(0.05), Inches(3.0), Inches(0.25),
                     f"{name}  —  {role}", font_size=13, color=accent, bold=True)
        add_text_box(slide, Inches(MARGIN + 0.2), y + Inches(0.3), Inches(2.8), Inches(0.22),
                     org, font_size=10, color=MID_GREY)
        add_text_box(slide, Inches(MARGIN + 3.5), y + Inches(0.08), Inches(5.0), Inches(0.25),
                     f"Red Lines: {red_lines}", font_size=10, color=LIGHT_GREY)
        add_text_box(slide, Inches(MARGIN + 3.5), y + Inches(0.35), Inches(5.0), Inches(0.22),
                     f"Trigger Event: {trigger_event}", font_size=10, color=DANGER_RED)
        # Escalation stages
        add_text_box(slide, Inches(SLIDE_W - 3.5), y + Inches(0.15), Inches(2.8), Inches(0.5),
                     "dormant > watching >\nagitated > hostile > triggered",
                     font_size=9, color=MID_GREY, alignment=PP_ALIGN.RIGHT)
        y += Inches(0.95)

    # Cascade note
    add_rounded_card(slide, Inches(MARGIN), Inches(6.55), Inches(CARD_FULL_W), Inches(0.55),
                     CARD_BG, ACCENT_GOLD)
    add_text_box(slide, Inches(MARGIN + 0.3), Inches(6.6), Inches(CARD_FULL_W - 0.6), Inches(0.45),
                 "CASCADE EFFECT: When one agent triggers, it drags connected agents -10 to -15 tolerance. "
                 "Interference pairs (e.g. Journalist + Regulator) accelerate each other's decay by 25-40%.",
                 font_size=11, color=ACCENT_GOLD)


def slide_materiality_matrix(prs):
    """Slide: CSRD Double Materiality Matrix."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "CSRD DOUBLE MATERIALITY MATRIX", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.5),
                 "In Round 2, you perform a Double Materiality Assessment under the CSRD framework. "
                 "Drag ESG issues onto a 4-quadrant matrix to determine which are material:",
                 font_size=14, color=LIGHT_GREY)

    # 4-quadrant layout
    quad_w = HALF_W
    quad_h = Inches(1.8)
    quads = [
        ("Q1: PRIORITISE & ALLOCATE", "Top-Right: High Financial + High Impact\n"
         "DOUBLE MATERIAL — Report under ESRS.\nCapEx deducted from CSF pool.",
         SUCCESS_GREEN, Inches(RIGHT_X), Inches(1.75)),
        ("Q2: MONITOR & ENGAGE", "Top-Left: Low Financial + High Impact\n"
         "IMPACT MATERIAL — Report Impact only.\nStrategic watch list.",
         RGBColor(0x33, 0x98, 0xDB), Inches(MARGIN), Inches(1.75)),
        ("Q3: WATCH & MANAGE", "Bottom-Right: High Financial + Low Impact\n"
         "FINANCIALLY MATERIAL — Report Risk.\nManage for enterprise value.",
         RGBColor(0xF3, 0x9C, 0x12), Inches(RIGHT_X), Inches(3.65)),
        ("Q4: LOW PRIORITY", "Bottom-Left: Low Financial + Low Impact\n"
         "NOT MATERIAL — Monitor only.\nNo ESRS reporting required.",
         MID_GREY, Inches(MARGIN), Inches(3.65)),
    ]

    for title, desc, accent, x, y in quads:
        add_rounded_card(slide, x, y, Inches(quad_w), quad_h, CARD_BG, accent)
        add_text_box(slide, x + Inches(0.2), y + Inches(0.1), Inches(quad_w - 0.4), Inches(0.3),
                     title, font_size=13, color=accent, bold=True)
        add_text_box(slide, x + Inches(0.2), y + Inches(0.45), Inches(quad_w - 0.4), Inches(1.2),
                     desc, font_size=11, color=LIGHT_GREY)

    # Axis labels
    add_text_box(slide, Inches(MARGIN), Inches(5.55), Inches(CONTENT_W), Inches(0.3),
                 "X-Axis: Financial Materiality (Enterprise Value)    |    "
                 "Y-Axis: Impact Materiality (People & Planet)",
                 font_size=12, color=MID_GREY, alignment=PP_ALIGN.CENTER)

    # Features row
    features = [
        ("Issue Bank", "15+ pre-loaded ESG issues tagged\nE / S / G with ESRS topics, severity,\nand time horizons (ST / MT / LT).",
         ACCENT_TEAL),
        ("Stakeholder Panel", "Commission a survey ($1M+) to\nget expert issue ratings. Or use\nthe AI Advisor for free guidance.",
         RGBColor(0x9B, 0x59, 0xB6)),
        ("Q1 Budget Link", "Issues placed in Q1 have their\nmitigation cost deducted from your\nCSF pool. Budget is enforced.",
         ACCENT_GOLD),
        ("Custom Factors", "Add your own ESG factors to the\nIssue Bank. Tag them by category\nand drag into any quadrant.",
         SUCCESS_GREEN),
    ]

    fw = (CARD_FULL_W - 0.6) / 4
    for i, (title, desc, accent) in enumerate(features):
        x = Inches(MARGIN + i * (fw + 0.2))
        add_rounded_card(slide, x, Inches(5.95), Inches(fw), Inches(1.15), CARD_BG, accent)
        add_text_box(slide, x + Inches(0.1), Inches(6.0), Inches(fw - 0.2), Inches(0.25),
                     title, font_size=11, color=accent, bold=True, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.1), Inches(6.28), Inches(fw - 0.2), Inches(0.75),
                     desc, font_size=9, color=LIGHT_GREY, alignment=PP_ALIGN.CENTER)


def slide_shadow_board_audit(prs):
    """Slide: Mid-Term Board Audit & Review (Shadow Board R5)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "MID-TERM BOARD AUDIT & REVIEW", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.5),
                 "At Round 5, the Shadow Board convenes. Three AI personas present conflicting arguments "
                 "about a climate crisis. You must publicly reject ONE — revealing your strategic DNA:",
                 font_size=14, color=LIGHT_GREY)

    # Three personas
    personas = [
        ("Marcus Chen-Hoffmann", "CIO, Nordic Pension Alliance",
         "'Minimise CAPEX. Choose Insurance Only ($2M). Every dollar of CAPEX\n"
         "is a dollar that won't flow to the dividend ratchet.'",
         "Reject = Sustainability-First archetype",
         "Hostile Takeover pathway risk increases",
         RGBColor(0xF5, 0x9E, 0x0B)),
        ("Megha Patrike", "Head Panchayat, Deccan Council",
         "'Choose Nature-Based Solutions ($5M). Hard engineering spikes our\n"
         "Natural Capital Debt. Nature IS the infrastructure.'",
         "Reject = Profit-Maximiser archetype",
         "Climate Black Swan / Stakeholder Revolt risk increases",
         RGBColor(0x10, 0xB9, 0x81)),
        ("Commissioner Carson", "EU DG FISMA",
         "'Option A — Hard Engineering ($8M) offers 85% resilience factor.\n"
         "Choosing less is a failure of risk management.'",
         "Reject = Risk-Taker archetype",
         "Regulatory Shutdown pathway risk increases",
         RGBColor(0x63, 0x66, 0xF1)),
    ]

    third_w = (CARD_FULL_W - 0.4) / 3
    for i, (name, title, script, archetype, cascade, accent) in enumerate(personas):
        x = Inches(MARGIN + i * (third_w + 0.2))
        add_rounded_card(slide, x, Inches(1.7), Inches(third_w), Inches(3.3), CARD_BG, accent)
        add_text_box(slide, x + Inches(0.15), Inches(1.78), Inches(third_w - 0.3), Inches(0.25),
                     name, font_size=13, color=accent, bold=True)
        add_text_box(slide, x + Inches(0.15), Inches(2.05), Inches(third_w - 0.3), Inches(0.22),
                     title, font_size=10, color=MID_GREY)
        add_text_box(slide, x + Inches(0.15), Inches(2.35), Inches(third_w - 0.3), Inches(1.2),
                     script, font_size=10, color=LIGHT_GREY)
        add_text_box(slide, x + Inches(0.15), Inches(3.65), Inches(third_w - 0.3), Inches(0.25),
                     archetype, font_size=10, color=accent, bold=True)
        add_text_box(slide, x + Inches(0.15), Inches(3.95), Inches(third_w - 0.3), Inches(0.5),
                     cascade, font_size=9, color=DANGER_RED)

    # Consequences section
    add_text_box(slide, Inches(MARGIN), Inches(5.2), Inches(CONTENT_W), Inches(0.3),
                 "CONSEQUENCES OF YOUR REJECTION", font_size=15, color=ACCENT_GOLD, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(5.55), Inches(3), ACCENT_GOLD)

    consequences = [
        ("Strategic Archetype Set", "Your rejection permanently classifies Muressons' strategic DNA "
         "(Sustainability-First / Profit-Maximiser / Risk-Taker)."),
        ("Hidden Flags Planted", "Flags like 'shareholder_alienated' or 'planet_expendable' are set silently. "
         "They cascade into Round 10's ending pathway."),
        ("Agent Tolerance -10", "The rejected persona's stakeholder agent loses 10 tolerance immediately. "
         "Decay rate may accelerate by 20%."),
        ("Consequence DNA", "A causal chain is recorded in the DNA Visualizer: Decision > Effect > R10 Risk."),
    ]

    y = Inches(5.7)
    for title, desc in consequences:
        add_text_box(slide, Inches(MARGIN + 0.2), y, Inches(3.0), Inches(0.22),
                     title, font_size=11, color=WHITE, bold=True)
        add_text_box(slide, Inches(MARGIN + 3.5), y, Inches(CONTENT_W - 4.0), Inches(0.22),
                     desc, font_size=10, color=LIGHT_GREY)
        y += Inches(0.28)

    add_rounded_card(slide, Inches(MARGIN), Inches(6.9), Inches(CARD_FULL_W), Inches(0.45),
                     CARD_BG, MID_GREY)
    add_text_box(slide, Inches(MARGIN + 0.3), Inches(6.93), Inches(CARD_FULL_W - 0.6), Inches(0.35),
                 "Theory: Mitchell et al. (1997) Stakeholder Salience  |  Schon (1983) Reflection-in-Action  |  "
                 "Hirschman (1970) Exit, Voice, Loyalty",
                 font_size=10, color=MID_GREY)


def slide_investment_guidelines(prs):
    """Slide: Investment Strategy Guidelines."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "INVESTMENT STRATEGY GUIDELINES", font_size=36, color=ACCENT_GOLD, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4), ACCENT_GOLD)

    # Left column: CSF Mechanics
    add_text_box(slide, Inches(MARGIN), Inches(1.2), Inches(HALF_W), Inches(0.35),
                 "CSF POOL MECHANICS", font_size=16, color=ACCENT_TEAL, bold=True)

    mechanics = [
        ("Starting Pool", "$10M per round, adjusted by\nperformance and crisis impacts."),
        ("100% Target", "Allocate within your pool for zero\ninterest cost. Optimal baseline."),
        ("120% Credit Cap", "You CAN over-allocate up to 120%\nof your pool — the excess is borrowed\nat punitive interest rates."),
        ("Under-Allocation", "Unspent CSF is retained but unused\ncapital = missed growth opportunity."),
        ("Carbon Tax", "Deducted from EBITDA, not treasury.\nGrows each round. Decarbonise early."),
    ]

    y = Inches(1.6)
    for title, desc in mechanics:
        add_rounded_card(slide, Inches(MARGIN), y, Inches(HALF_W), Inches(0.8), CARD_BG, ACCENT_TEAL)
        add_text_box(slide, Inches(MARGIN + 0.2), y + Inches(0.05), Inches(2.0), Inches(0.25),
                     title, font_size=12, color=ACCENT_TEAL, bold=True)
        add_text_box(slide, Inches(MARGIN + 2.3), y + Inches(0.08), Inches(HALF_W - 2.7), Inches(0.6),
                     desc, font_size=10, color=LIGHT_GREY)
        y += Inches(0.85)

    # Right column: Strategic Allocation Principles
    add_text_box(slide, Inches(RIGHT_X), Inches(1.2), Inches(HALF_W), Inches(0.35),
                 "ALLOCATION PRINCIPLES", font_size=16, color=ACCENT_GOLD, bold=True)

    principles = [
        ("Protect Revenue Engines", "Pharma ($18M) and Electronics ($16.5M)\n"
         "generate 65% of group revenue. Under-\ninvesting crashes top-line growth.",
         ACCENT_TEAL),
        ("Build Synergy", "Aligned investments across BUs unlock\n"
         "the Synergy Multiplier — an OPEX\nreduction that compounds over rounds.",
         SUCCESS_GREEN),
        ("Front-Load Decarbonisation", "Early carbon reduction avoids the\n"
         "exponentially growing carbon tax.\n$1 spent in R2 saves $3 by R8.",
         RGBColor(0x33, 0x98, 0xDB)),
        ("Reserve for Crises", "Keep a buffer for unexpected shocks.\n"
         "Rounds 4-5 often hit treasury hard.\nA $3-5M reserve is prudent.",
         RGBColor(0xF3, 0x9C, 0x12)),
        ("Watch Governance Risk", "High governance risk reduces cash\n"
         "conversion efficiency. Every 10pts of\ngov risk = ~3% EBITDA drag.",
         RGBColor(0x9B, 0x59, 0xB6)),
    ]

    y = Inches(1.6)
    for title, desc, accent in principles:
        add_rounded_card(slide, Inches(RIGHT_X), y, Inches(HALF_W), Inches(0.8), CARD_BG, accent)
        add_text_box(slide, Inches(RIGHT_X + 0.2), y + Inches(0.05), Inches(2.2), Inches(0.25),
                     title, font_size=12, color=accent, bold=True)
        add_text_box(slide, Inches(RIGHT_X + 2.5), y + Inches(0.08), Inches(HALF_W - 2.9), Inches(0.6),
                     desc, font_size=10, color=LIGHT_GREY)
        y += Inches(0.85)

    # Bottom warning
    add_rounded_card(slide, Inches(MARGIN), Inches(6.2), Inches(CARD_FULL_W), Inches(0.55),
                     CARD_BG, DANGER_RED)
    add_text_box(slide, Inches(MARGIN + 0.3), Inches(6.25), Inches(CARD_FULL_W - 0.6), Inches(0.45),
                 "WARNING: Over-leveraging (>100%) triggers emergency credit. The interest compounds each "
                 "round and is deducted from treasury. Two consecutive rounds at 120% can create a death spiral.",
                 font_size=12, color=DANGER_RED)

    add_text_box(slide, Inches(MARGIN), Inches(6.9), Inches(CONTENT_W), Inches(0.3),
                 "The best strategies balance growth investment, ESG compliance, and treasury preservation.",
                 font_size=12, color=MID_GREY, alignment=PP_ALIGN.CENTER)


def slide_learning_outcomes(prs):
    """Slide: Learning Outcomes."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    add_text_box(slide, Inches(MARGIN), Inches(0.3), Inches(CONTENT_W), Inches(0.6),
                 "LEARNING OUTCOMES", font_size=36, color=ACCENT_TEAL, bold=True)
    add_accent_line(slide, Inches(MARGIN), Inches(0.95), Inches(4))

    add_text_box(slide, Inches(MARGIN), Inches(1.1), Inches(CONTENT_W), Inches(0.4),
                 "By the end of this simulation, you will have developed competencies across "
                 "6 critical dimensions of corporate sustainability leadership:",
                 font_size=14, color=LIGHT_GREY)

    outcomes = [
        ("Strategic Thinking",
         "Understand trade-offs between short-term financial performance and long-term "
         "sustainability value creation. Navigate the tension between shareholder returns "
         "and stakeholder capitalism.",
         "Rounds 1-10: Every A/B/C decision tests this",
         ACCENT_TEAL),
        ("CSRD & Double Materiality",
         "Apply the EU Corporate Sustainability Reporting Directive framework. Classify "
         "ESG issues by financial materiality and impact materiality using ESRS topic "
         "standards (E1-E5, S1-S4, G1).",
         "Round 2: Double Materiality Matrix minigame",
         RGBColor(0x33, 0x98, 0xDB)),
        ("Stakeholder Salience",
         "Evaluate competing stakeholder claims using Mitchell et al.'s framework of "
         "Power, Legitimacy, and Urgency. Understand how stakeholder agents escalate "
         "from dormant to triggered.",
         "Round 5: Shadow Board Audit | All rounds: Agent system",
         RGBColor(0x9B, 0x59, 0xB6)),
        ("Systems Thinking",
         "Recognise cross-round causal dependencies and feedback loops. Understand how "
         "decisions in early rounds create path dependencies that constrain options in "
         "later rounds (Meadows' Leverage Points).",
         "Round 5+: Consequence DNA Visualizer",
         RGBColor(0xF3, 0x9C, 0x12)),
        ("Climate & Carbon Literacy",
         "Manage carbon intensity, natural capital debt, Scope 1/2/3 emissions, and "
         "carbon credit markets. Understand the financial impact of carbon taxation "
         "and stranded asset risk.",
         "Rounds 3, 5, 7: Carbon-focused crises",
         SUCCESS_GREEN),
        ("Ethical Leadership",
         "Navigate moral dilemmas where profit-maximising and ethically-sound choices "
         "diverge. Articulate your reasoning under pressure in the CEO Interview. "
         "Develop a personal ethical framework for corporate decision-making.",
         "Round 10: CEO Interview | All rounds: Option C tests",
         DANGER_RED),
    ]

    y = Inches(1.6)
    for title, desc, evidence, accent in outcomes:
        add_rounded_card(slide, Inches(MARGIN), y, Inches(CARD_FULL_W), Inches(0.82), CARD_BG, accent)
        add_text_box(slide, Inches(MARGIN + 0.2), y + Inches(0.05), Inches(3.0), Inches(0.25),
                     title, font_size=13, color=accent, bold=True)
        add_text_box(slide, Inches(MARGIN + 3.5), y + Inches(0.05), Inches(CARD_FULL_W - 4.0), Inches(0.35),
                     desc, font_size=10, color=LIGHT_GREY)
        add_text_box(slide, Inches(MARGIN + 3.5), y + Inches(0.45), Inches(CARD_FULL_W - 4.0), Inches(0.25),
                     evidence, font_size=9, color=MID_GREY)
        y += Inches(0.88)

    # Bloom's taxonomy note
    add_rounded_card(slide, Inches(MARGIN), Inches(6.9), Inches(CARD_FULL_W), Inches(0.45),
                     CARD_BG, MID_GREY)
    add_text_box(slide, Inches(MARGIN + 0.3), Inches(6.93), Inches(CARD_FULL_W - 0.6), Inches(0.35),
                 "Pedagogy: Simulation covers Bloom's Taxonomy levels 3-6 (Apply, Analyse, Evaluate, Create)  |  "
                 "Kolb Experiential Learning  |  Schon Reflection-in-Action",
                 font_size=10, color=MID_GREY)


def slide_closing(prs):
    """Slide 25: Ready to Begin."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_dark_background(slide)

    cx = SLIDE_W / 2
    line_w = 6.0

    add_accent_line(slide, Inches(cx - line_w / 2), Inches(2.2), Inches(line_w))

    add_text_box(slide, Inches(MARGIN), Inches(2.4), Inches(CONTENT_W), Inches(0.8),
                 "READY TO LEAD?", font_size=48, color=ACCENT_TEAL,
                 bold=True, alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Inches(1), Inches(3.3), Inches(SLIDE_W - 2), Inches(0.5),
                 "The Board of Muressons Global awaits your strategic direction.",
                 font_size=20, color=WHITE, alignment=PP_ALIGN.CENTER)

    add_accent_line(slide, Inches(cx - line_w / 2), Inches(4.0), Inches(line_w))

    reminders = [
        "10 Rounds  |  5 Years  |  Every Decision Counts",
        "Profit without purpose is a stranded asset",
        "Purpose without profit is a failed enterprise",
    ]
    y = Inches(4.4)
    for r in reminders:
        add_text_box(slide, Inches(1), y, Inches(SLIDE_W - 2), Inches(0.35),
                     r, font_size=16, color=LIGHT_GREY, alignment=PP_ALIGN.CENTER)
        y += Inches(0.4)

    add_text_box(slide, Inches(1), Inches(5.7), Inches(SLIDE_W - 2), Inches(0.4),
                 "Good luck, Director.", font_size=22, color=ACCENT_GOLD,
                 bold=True, alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Inches(1), Inches(6.5), Inches(SLIDE_W - 2), Inches(0.3),
                 "MURESSONS GLOBAL  |  Sovereign Intelligence Systems",
                 font_size=12, color=MID_GREY, alignment=PP_ALIGN.CENTER)


# =====================================================================
# MAIN
# =====================================================================

def main():
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)

    print("Building Muressons Player Briefing (16:9 Widescreen)...")

    slide_title(prs);                  print("  [+] Slide 1: Title")
    slide_overview(prs);               print("  [+] Slide 2: Overview")
    slide_business_units(prs);         print("  [+] Slide 3: Business Units")
    slide_login(prs);                  print("  [+] Slide 4: Login")
    slide_cockpit(prs);                print("  [+] Slide 5: Executive Cockpit")
    slide_kpis(prs);                   print("  [+] Slide 6: KPIs")
    slide_round_flow(prs);             print("  [+] Slide 7: Round Flow")
    slide_investment_matrix(prs);      print("  [+] Slide 8: Investment Matrix")
    slide_investment_guidelines(prs);  print("  [+] Slide 9: Investment Strategy Guidelines")
    slide_roadmap(prs);                print("  [+] Slide 10: 10-Round Roadmap")
    slide_minigames(prs);              print("  [+] Slide 11: Minigames")
    slide_stakeholder_matrix(prs);     print("  [+] Slide 12: Stakeholder Analysis Matrix")
    slide_materiality_matrix(prs);     print("  [+] Slide 13: CSRD Double Materiality Matrix")
    slide_shadow_board_audit(prs);     print("  [+] Slide 14: Mid-Term Board Audit")
    slide_terminal_valuation(prs);     print("  [+] Slide 15: Terminal Valuation")
    slide_archetypes(prs);             print("  [+] Slide 16: Archetypes")
    slide_strategy_tips(prs);          print("  [+] Slide 17: Strategy Tips")
    slide_strategic_pillars(prs);      print("  [+] Slide 18: Strategic Pillars")
    slide_alternate_pathways(prs);     print("  [+] Slide 19: Alternate Pathways")
    slide_pathway_activist(prs);       print("  [+] Slide 20: Pathway - Activist Ultimatum")
    slide_pathway_climate(prs);        print("  [+] Slide 21: Pathway - Climate Black Swan")
    slide_pathway_stakeholder(prs);    print("  [+] Slide 22: Pathway - Stakeholder Revolt")
    slide_pathway_takeover(prs);       print("  [+] Slide 23: Pathway - Hostile Takeover")
    slide_pathway_regulatory(prs);     print("  [+] Slide 24: Pathway - Regulatory Shutdown")
    slide_sankey_diagram(prs);         print("  [+] Slide 25: Sankey Diagram")
    slide_endgame(prs);                print("  [+] Slide 26: The Endgame")
    slide_balanced_scorecard(prs);     print("  [+] Slide 27: Balanced Scorecard")
    slide_ceo_interview(prs);          print("  [+] Slide 28: CEO Interview")
    slide_learning_outcomes(prs);      print("  [+] Slide 29: Learning Outcomes")
    slide_closing(prs);                print("  [+] Slide 30: Closing")

    prs.save(OUTPUT)
    print(f"\nSaved: {OUTPUT}")
    print(f"  {len(prs.slides)} slides generated")


if __name__ == "__main__":
    main()
