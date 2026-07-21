"""
Muressons Documentation Suite Builder  (pandoc edition)
Converts Markdown sources → Word DOCX using pandoc with native LaTeX math (OMML).

Requires:
  - pandoc >= 3.0 on PATH  (winget install JohnMacFarlane.Pandoc)
  - scripts/reference.docx  (run make_reference_docx.py once to generate)

Run: python scripts/build_word_docs.py
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime, UTC

# Force UTF-8 on stdout/stderr so pandoc warnings with emoji don't
# crash print() on Windows cp1252 consoles.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BRAIN_DIR   = r"C:\Users\Home\.gemini\antigravity-ide\brain\998100d0-6b26-4528-b796-07bbe5278802"
OUTPUT_DIR  = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim\docs"
REFERENCE   = os.path.join(SCRIPT_DIR, "reference.docx")

# ── Document registry (ordered by audience priority) ─────────────────────────
FILES = [
    # Audience: Executive
    ("full_user_guide.md",         "Muressons_Executive_User_Guide.docx"),
    # Audience: Facilitator
    ("full_facilitator_manual.md", "Muressons_Facilitator_Operations_Manual.docx"),
    ("full_scoring_guide.md",      "Muressons_Assessment_and_Scoring_Guide.docx"),
    # Audience: Platform Admin
    ("full_admin_guide.md",        "Muressons_God_Mode_Administration_Guide.docx"),
    # Audience: All
    ("full_glossary.md",           "Muressons_ESG_Sustainability_Glossary.docx"),
    # Audience: Developer
    ("full_cheatsheet.md",         "Muressons_Developer_Cheatsheet.docx"),
    ("full_deployment_guide.md",   "Muressons_Deployment_Infrastructure_Guide.docx"),
    ("full_api_reference.md",      "Muressons_API_Reference.docx"),
    # Audience: Architect
    ("full_sad.md",                "Muressons_System_Architecture.docx"),
    ("full_mindmap.md",            "Muressons_Technical_Hierarchy.docx"),
    # Audience: Curriculum Designer
    ("full_sdd.md",                "Muressons_Simulation_Design_Document.docx"),
]

# ── Pandoc invocation ─────────────────────────────────────────────────────────
def build_docx(md_path: str, docx_path: str) -> bool:
    """
    Convert a Markdown file to DOCX via pandoc.

    Key pandoc flags:
      -f markdown+tex_math_dollars   : parse $inline$ and $$display$$ LaTeX
      --mathml                       : convert math to MathML (Word renders natively)
      --reference-doc                : apply Muressons brand styles
      --toc                          : insert table of contents
      --toc-depth=3                  : H1, H2, H3 in TOC
      -V geometry:margin=1in        : page margins
    """
    pandoc_exe = shutil.which("pandoc")
    if not pandoc_exe:
        # Try common install locations on Windows
        candidates = [
            r"C:\Program Files\Pandoc\pandoc.exe",
            r"C:\Users\Home\AppData\Local\Pandoc\pandoc.exe",
        ]
        for c in candidates:
            if os.path.exists(c):
                pandoc_exe = c
                break
    if not pandoc_exe:
        print("  ERROR: pandoc not found on PATH. Run: winget install JohnMacFarlane.Pandoc")
        return False

    cmd = [
        pandoc_exe,
        md_path,
        "-f", "markdown+tex_math_dollars+smart",
        "-t", "docx",
        "--mathml",
        "--toc",
        "--toc-depth=3",
        "-o", docx_path,
    ]

    # Use reference.docx if it exists
    if os.path.exists(REFERENCE):
        cmd += ["--reference-doc", REFERENCE]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )

    if result.returncode != 0:
        print(f"  ERROR (pandoc exit {result.returncode}):")
        stderr = result.stderr or ""
        for line in stderr.strip().splitlines():
            print(f"    {line}")
        return False

    stderr = result.stderr or ""
    if stderr.strip():
        # pandoc may emit warnings (not errors) on stderr
        for line in stderr.strip().splitlines():
            if line.strip():
                print(f"  WARN: {line}")

    return True


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Building {len(FILES)} Word documents into: {OUTPUT_DIR}\n")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate reference.docx if missing
    if not os.path.exists(REFERENCE):
        make_script = os.path.join(SCRIPT_DIR, "make_reference_docx.py")
        if os.path.exists(make_script):
            print("Generating reference.docx style template...")
            subprocess.run([sys.executable, make_script], check=True)
        else:
            print("  WARNING: reference.docx not found and make_reference_docx.py missing.")
            print("  Pandoc will use its built-in default styles.\n")

    success = 0
    for md_file, docx_file in FILES:
        md_path   = os.path.join(BRAIN_DIR, md_file)
        docx_path = os.path.join(OUTPUT_DIR, docx_file)

        if not os.path.exists(md_path):
            print(f"Processing: {md_file}\n  SKIP (not found)")
            continue

        print(f"Processing: {md_file}")
        ok = build_docx(md_path, docx_path)
        if ok:
            size_kb = round(os.path.getsize(docx_path) / 1024, 1)
            print(f"  OK: {docx_file}  ({size_kb} KB)")
            success += 1
        # else: error already printed by build_docx

    print(f"\nDone. {success}/{len(FILES)} documents generated successfully.")
