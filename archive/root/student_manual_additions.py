"""
Student Manual v3 — Additional sections: §12 Case Studies, Expanded Glossary, Appendix D.
Called from the main generator after build_part2.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from student_manual_helpers import *
from real_world_parallels import REAL_WORLD_PARALLELS
from admin_analytics import _glossary_terms

IMG = os.path.join(os.path.dirname(__file__), 'guide_images')

# Academic references for Appendix D
REFERENCES = [
    ("Anderson, R.C.", 2009, "Confessions of a Radical Industrialist", "St. Martin's Press"),
    ("Barney, J.B.", 1991, "Firm Resources and Sustained Competitive Advantage", "Journal of Management, 17(1), 99-120"),
    ("Carbon Tracker Initiative", 2013, "Unburnable Carbon: Are the World's Financial Markets Carrying a Carbon Bubble?", "Carbon Tracker"),
    ("Costanza, R. et al.", 1997, "The Value of the World's Ecosystem Services and Natural Capital", "Nature, 387, 253-260"),
    ("Dastin, J.", 2018, "Amazon Scraps Secret AI Recruiting Tool That Showed Bias Against Women", "Reuters"),
    ("DiMaggio, P.J. & Powell, W.W.", 1983, "The Iron Cage Revisited: Institutional Isomorphism", "American Sociological Review, 48(2), 147-160"),
    ("Dixit, A.K. & Pindyck, R.S.", 1994, "Investment Under Uncertainty", "Princeton University Press"),
    ("Ellen MacArthur Foundation", 2013, "Towards the Circular Economy", "Ellen MacArthur Foundation"),
    ("European Commission", 2022, "Corporate Sustainability Reporting Directive (CSRD)", "EUR-Lex, Directive 2022/2464"),
    ("European Parliament", 2024, "EU Artificial Intelligence Act", "Regulation 2024/1689"),
    ("Freeman, R.E.", 1984, "Strategic Management: A Stakeholder Approach", "Pitman Publishing"),
    ("GHG Protocol", 2011, "Corporate Value Chain (Scope 3) Accounting Standard", "World Resources Institute"),
    ("Hardin, G.", 1968, "The Tragedy of the Commons", "Science, 162(3859), 1243-1248"),
    ("ICMA", 2021, "Green Bond Principles", "International Capital Market Association"),
    ("ILO", 2015, "Guidelines for a Just Transition Towards Sustainable Economies", "International Labour Organization"),
    ("Kahneman, D. & Tversky, A.", 1979, "Prospect Theory: An Analysis of Decision Under Risk", "Econometrica, 47(2), 263-291"),
    ("Keller, K.L.", 1993, "Conceptualizing, Measuring, and Managing Customer-Based Brand Equity", "Journal of Marketing, 57(1), 1-22"),
    ("Kolb, D.A.", 1984, "Experiential Learning", "Prentice-Hall"),
    ("Lieberman, M.B. & Montgomery, D.B.", 1988, "First-Mover Advantages", "Strategic Management Journal, 9(S1), 41-58"),
    ("Locke, R.M.", 2003, "The Promise and Perils of Globalization: The Case of Nike", "MIT Working Paper"),
    ("Mendelow, A.L.", 1991, "Stakeholder Mapping", "Proceedings of the 2nd International Conference on Information Systems"),
    ("Mitchell, R.K., Agle, B.R. & Wood, D.J.", 1997, "Toward a Theory of Stakeholder Identification and Salience", "Academy of Management Review, 22(4), 853-886"),
    ("OECD", 2015, "G20/OECD Principles of Corporate Governance", "OECD Publishing"),
    ("Porter, M.E. & Kramer, M.R.", 2011, "Creating Shared Value", "Harvard Business Review, 89(1/2), 62-77"),
    ("Rawls, J.", 1971, "A Theory of Justice", "Harvard University Press"),
    ("Schlosberg, D.", 2007, "Defining Environmental Justice", "Oxford University Press"),
    ("Sen, A.", 1999, "Development as Freedom", "Oxford University Press"),
    ("Senge, P.", 1990, "The Fifth Discipline: The Art and Practice of the Learning Organization", "Currency Doubleday"),
    ("Solomon, R.C.", 1992, "Ethics and Excellence: Cooperation and Integrity in Business", "Oxford University Press"),
    ("Suchman, M.C.", 1995, "Managing Legitimacy: Strategic and Institutional Approaches", "Academy of Management Review, 20(3), 571-610"),
    ("Taleb, N.N.", 2012, "Antifragile: Things That Gain from Disorder", "Random House"),
    ("Teece, D.J.", 1997, "Dynamic Capabilities and Strategic Management", "Strategic Management Journal, 18(7), 509-533"),
    ("Thomson, I. & Boutilier, R.", 2011, "The Social License to Operate", "SME Mining Engineering Handbook"),
    ("UN PRI", 2006, "Principles for Responsible Investment", "United Nations Environment Programme"),
    ("Unilever PLC", 2020, "Sustainable Living Plan: 10 Years' Progress", "Unilever"),
    ("US EPA", 2015, "Notice of Violation to Volkswagen AG", "US Environmental Protection Agency"),
    ("WHO", 2019, "Burn-out: An Occupational Phenomenon (ICD-11)", "World Health Organization"),
]


def build_case_studies(doc):
    """§12: Real-World Case Studies mapped to simulation rounds."""
    h(doc, '12. Real-World Case Studies', 1)
    body(doc, 'Each simulation round parallels a real corporate event. Studying these cases deepens your understanding of the strategic trade-offs you face in the simulation.')

    for rnd in range(1, 11):
        case = REAL_WORLD_PARALLELS.get(rnd, {})
        if not case:
            continue
        icon = case.get('icon', '')
        title = case.get('title', '')
        company = case.get('company', '')

        h(doc, f"Case {rnd}: {icon} {title}", 2)
        body(doc, f"Company: {company} | Simulation Parallel: Round {rnd} — {case.get('dilemma', '')}", bold=True)

        # Brief description
        body(doc, 'What Happened:', bold=True)
        body(doc, case.get('brief', ''))

        # Simulation connection
        body(doc, 'Connection to the Simulation:', bold=True)
        body(doc, case.get('simulation_parallel', ''))

        # Outcome
        body(doc, 'Real-World Outcome:', bold=True)
        body(doc, case.get('outcome', ''))

        # Key lesson
        body(doc, f"Key Lesson: {case.get('key_lesson', '')}", bold=True, italic=True)

        # Theory link
        theory = case.get('theory_link', '')
        if theory:
            body(doc, f"Theory: {theory}", italic=True)

        # Reference
        ref = case.get('reference', '')
        if ref:
            body(doc, f"Reference: {ref}", italic=True, size=9)

        spacer(doc)
    page_break(doc)


def build_expanded_glossary(doc):
    """§14: Full 50-term glossary from backend with references."""
    h(doc, '14. Glossary of Key Terms', 1)
    body(doc, 'This glossary contains all 50 terms used across the simulation, organised alphabetically. Where available, academic or regulatory references are provided.')

    # Group by category
    categories = {
        'Financial Metrics': ['finance', 'profitability', 'treasury', 'valuation', 'capital'],
        'Sustainability & ESG': ['esg', 'environment', 'social', 'sustainability', 'natural capital'],
        'Simulation Engines': ['engine', 'contagion', 'synergy', 'decay', 'stochastic'],
        'Scoring & Archetypes': ['scoring', 'archetype', 'multiplier'],
        'Frameworks & Regulation': ['regulation', 'governance', 'csrd', 'tcfd', 'framework'],
        'Simulation Mechanics': ['mechanics', 'flags', 'system', 'paradigm', 'decisions'],
    }

    # Sort all terms alphabetically
    sorted_terms = sorted(_glossary_terms, key=lambda t: t.get('term', '').lower())

    for term_data in sorted_terms:
        term = term_data.get('term', '')
        defn = term_data.get('definition', '')
        weblink = term_data.get('weblink', '')
        tags = term_data.get('tags', [])

        p = doc.add_paragraph()
        r = p.add_run(f"{term}: ")
        r.bold = True
        r.font.size = Pt(11)
        r = p.add_run(defn)
        r.font.size = Pt(10)
        r.font.color.rgb = DARK_GRAY

        if weblink:
            p2 = doc.add_paragraph()
            r2 = p2.add_run(f"    Reference: {weblink}")
            r2.font.size = Pt(8)
            r2.italic = True
            r2.font.color.rgb = RGBColor(0x55, 0x55, 0x99)

    page_break(doc)


def build_appendix_d(doc):
    """Appendix D: Further Reading & Academic References."""
    h(doc, 'Appendix D: Further Reading & Academic References', 2)
    body(doc, 'The following sources underpin the theoretical frameworks, regulatory models, and case studies used throughout the simulation. Students and facilitators are encouraged to consult these for deeper understanding.')

    for author, year, title, source in REFERENCES:
        p = doc.add_paragraph()
        r = p.add_run(f"{author} ({year}). ")
        r.bold = True
        r.font.size = Pt(10)
        r = p.add_run(f'"{title}." ')
        r.italic = True
        r.font.size = Pt(10)
        r = p.add_run(source)
        r.font.size = Pt(10)
        r.font.color.rgb = DARK_GRAY

    page_break(doc)
