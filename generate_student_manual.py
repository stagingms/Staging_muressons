"""
Muressons Global Corporation — Student Manual Generator
Main entry point: combines Part 1 + Part 2 into a single Word document.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from student_manual_helpers import create_doc
from student_manual_part1 import build_part1
from student_manual_part2 import build_part2

OUTPUT = os.path.join(os.path.dirname(__file__), 'Muressons_Student_Manual_v3.docx')

def main():
    print("=" * 60)
    print("  Muressons Global Corporation — Student Manual Generator")
    print("=" * 60)

    print("\n[1/3] Creating document structure...")
    doc = create_doc()

    print("[2/3] Building Part I-II (Sections 1-7)...")
    doc = build_part1(doc)

    print("[3/3] Building Part III-IV + Appendices (Sections 8-14)...")
    doc = build_part2(doc)

    print(f"\n[SAVE] Writing to: {OUTPUT}")
    doc.save(OUTPUT)
    print(f"[DONE] Student manual generated successfully!")
    print(f"       File: {OUTPUT}")
    print(f"       Size: {os.path.getsize(OUTPUT) / 1024:.0f} KB")

if __name__ == '__main__':
    main()
