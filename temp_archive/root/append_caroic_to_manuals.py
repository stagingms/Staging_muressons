import docx
import os
import glob

def append_to_doc(filepath, is_glossary=False):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    doc = docx.Document(filepath)
    
    if is_glossary:
        doc.add_heading('CAROIC (Carbon-Adjusted Return on Invested Capital)', level=2)
        doc.add_paragraph(
            "A hybrid financial-environmental metric that extends traditional ROIC by adding a shadow carbon cost to the denominator. "
            "Formula: CAROIC = EBITDA × (1 − Tax Rate) / (Invested Capital + (Carbon Tonnage × Shadow Carbon Price)). "
            "It penalizes carbon-intensive firms by artificially inflating their capital base, thereby compressing their return ratio. "
            "Graded on a scale from A+ (≥25%) to F (<0%)."
        )
    else:
        doc.add_page_break()
        doc.add_heading('Appendix: Understanding CAROIC', level=1)
        doc.add_paragraph(
            "As you navigate the simulation, one of the most critical metrics you will encounter on your Executive Cockpit is CAROIC "
            "(Carbon-Adjusted Return on Invested Capital). This metric bridges the gap between financial performance and environmental liability."
        )
        
        doc.add_heading('The Formula', level=2)
        p = doc.add_paragraph()
        p.add_run("CAROIC = [EBITDA × (1 − Tax Rate)] / [Invested Capital + (Carbon Tonnage × Shadow Carbon Price)]\n").font.name = 'Courier New'
        
        doc.add_heading('Why It Matters', level=2)
        doc.add_paragraph(
            "Traditional ROIC only measures the cash return on financial capital. CAROIC introduces a 'shadow carbon cost' "
            "(typically set to a high internal carbon price, such as $250/ton). This cost is added directly to your Invested Capital base. "
            "If your business unit generates high revenues but relies on heavily pollutive processes, the denominator of the CAROIC equation "
            "will balloon, compressing your return percentage."
        )
        
        doc.add_heading('Grading Scale', level=2)
        doc.add_paragraph("A+ : ≥ 25% (Exceptional carbon-financial efficiency)", style='List Bullet')
        doc.add_paragraph("A  : ≥ 15%", style='List Bullet')
        doc.add_paragraph("B  : ≥ 10%", style='List Bullet')
        doc.add_paragraph("C  : ≥ 5%", style='List Bullet')
        doc.add_paragraph("D  : ≥ 0%", style='List Bullet')
        doc.add_paragraph("F  : < 0% (Operating losses compounded by carbon liability)", style='List Bullet')
        
        doc.add_heading('Strategic Takeaway', level=2)
        doc.add_paragraph(
            "To achieve an A+ grade, you cannot simply increase EBITDA. You must concurrently invest in decarbonization "
            "(reducing Carbon Tonnage) to shrink the denominator. This makes it impossible to achieve top-tier CAROIC "
            "while maintaining a high carbon intensity."
        )

    # Save logic
    dir_name = os.path.dirname(filepath)
    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    new_filepath = os.path.join(dir_name, f"{name}_with_CAROIC{ext}")
    
    doc.save(new_filepath)
    print(f"Successfully appended CAROIC to {new_filepath}")

if __name__ == '__main__':
    base_dir = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim"
    
    # Target manuals (latest versions based on directory check)
    student_manual = os.path.join(base_dir, "Muressons_Student_Manual_v5.docx")
    
    append_to_doc(student_manual, is_glossary=False)
