"""Main DOCX Generator — Muressons Facilitator Manual."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from docx_styles import setup_doc, add_page_break
from gen_part1 import build_title_page, build_toc, build_section1, build_section2
from gen_section3 import build_section3_enhanced, build_architecture_diagram
from gen_part2 import build_section4
from gen_part3 import build_section5, build_section6, build_section7, build_section8, build_section9, build_section10, build_section10c
from gen_part4 import (build_dashboard_guide, build_god_mode_guide, build_pitfalls,
                        build_planning, build_assessment, build_faq,
                        build_appendix_a, build_appendix_b, build_appendix_c)
from gen_appendix_d import build_appendix_d

def main():
    print("Building Muressons Facilitator Manual (v3 — Enhanced Engines)...")
    doc = setup_doc()
    
    print("  Title page & TOC...")
    build_title_page(doc)
    build_toc(doc)
    
    print("  Part 1: Foundation & Engine...")
    build_section1(doc)
    build_architecture_diagram(doc)
    build_section2(doc)
    build_section3_enhanced(doc)
    
    print("  Part 2: Round-by-Round Guide...")
    build_section4(doc)
    
    print("  Part 3: Advanced Systems (§5-§10C)...")
    build_section5(doc)
    build_section6(doc)
    build_section7(doc)
    build_section8(doc)
    build_section9(doc)
    build_section10(doc)
    build_section10c(doc)
    
    print("  Part 4: Dashboard, Planning, Appendices...")
    build_dashboard_guide(doc)
    build_god_mode_guide(doc)
    build_pitfalls(doc)
    
    # §12 Quick Reference Cards
    add_page_break(doc)
    from docx_styles import add_styled_table, add_callout
    doc.add_heading(u'§12. Quick-Reference Cards', level=1)
    doc.add_heading('12.1 M_R Checklist', level=2)
    add_styled_table(doc, ['Round', 'Decision', 'M_R Bonus', 'Earned?'],
        [['R2', 'Full Materiality Alignment', '+0.10', '☐'],
         ['R3', 'Rapid Supplier Switch', '+0.15', '☐'],
         ['R4', 'Full Transparency', '+0.10', '☐'],
         ['R5', 'Nature-Based Solutions', '+0.20', '☐'],
         ['R6', 'Ethical AI Overhaul', '+0.15', '☐'],
         ['R7', 'Waste-to-Energy', '+0.30', '☐'],
         ['R9', 'Managed Transition', '+0.12', '☐'],
         ['R9', 'Community Fund', '+0.18', '☐'],
         ['R10', 'Instability Discount', '-0.40', '☐'],
         ['—', 'THEORETICAL MAX', '~2.10', '—']])
    
    doc.add_heading('12.2 Strike Probability Lookup', level=2)
    add_styled_table(doc, ['Burnout', 'SLO > 60', 'SLO 40-60', 'SLO < 40'],
        [['< 20%', '5%', '10%', '20%'],
         ['20-40%', '10%', '25%', '40%'],
         ['40-60%', '20%', '40%', '60%'],
         ['> 60%', '35%', '55%', '75%']])
    
    doc.add_heading('12.3 Archetype Thresholds', level=2)
    add_styled_table(doc, ['M_R Range', 'Default Name', 'Climate Pathway', 'Community Pathway'],
        [[u'≥ 1.80', 'Regenerative Titan', 'Climate Vanguard', 'Community Champion'],
         ['1.20-1.79', 'De-risked Safe Haven', 'Transition Leader', 'Stakeholder Partner'],
         ['0.80-1.19', 'Fragile Giant', 'Carbon Exposed', 'Social Debtor'],
         ['< 0.80', 'Stranded Relic', 'Climate Casualty', 'Community Antagonist']])
    
    build_planning(doc)
    build_assessment(doc)
    build_faq(doc)
    build_appendix_a(doc)
    build_appendix_b(doc)
    build_appendix_c(doc)
    build_appendix_d(doc)
    
    outpath = os.path.join(os.path.dirname(__file__), '..', 'Muressons_Facilitator_Manual_v2.docx')
    outpath = os.path.abspath(outpath)
    doc.save(outpath)
    print(f"\n[OK] Manual saved to: {outpath}")
    print(f"     Sections: 17 + 4 appendices (A, B, C, D — Architecture Blueprint)")
    print(f"     Estimated pages: 95-115")

if __name__ == '__main__':
    main()
