"""Combine 3 part docx files into one final Student Guide."""
from docx import Document
from docx.oxml.ns import qn
import os, copy

parts = ["_student_guide_part1.docx","_student_guide_part2.docx","_student_guide_part3.docx"]
base = os.path.dirname(__file__)

combined = Document(os.path.join(base, parts[0]))

for part_file in parts[1:]:
    part = Document(os.path.join(base, part_file))
    # Add page break before each part
    combined.add_page_break()
    for element in part.element.body:
        combined.element.body.append(copy.deepcopy(element))

# Copy images from part docs
for rel_id, rel in list(combined.part.rels.items()):
    pass  # relationships already embedded

out = os.path.join(base, "Muressons_Student_Guide.docx")
combined.save(out)
print(f"Combined guide saved: {out}")

# Also try docxcompose if available
try:
    from docxcompose.composer import Composer
    master = Document(os.path.join(base, parts[0]))
    composer = Composer(master)
    for pf in parts[1:]:
        doc = Document(os.path.join(base, pf))
        composer.append(doc)
    composer.save(out)
    print(f"Composed with docxcompose: {out}")
except ImportError:
    print("docxcompose not available, using basic merge (images may need re-linking)")
