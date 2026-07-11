"""
Muressons Global Corporation - Comprehensive Investment Strategy Report Generator
Merges three markdown strategy documents into one branded Word DOCX.

Sources (brain dir):
  investment_strategy_and_round_outcomes.md
  investment_strategy_balance_sheet_impact.md
  investment_strategy_share_price_impact.md

Output: docs/Muressons_Investment_Strategy_Comprehensive_Guide.docx

Run: python scripts/generate_strategy_report.py
"""

import os, sys, subprocess, shutil

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BRAIN_DIR  = r"c:\Users\Home\.gemini\antigravity\brain\4acca2b9-2b61-415e-8a20-2b6631e1d846"
OUTPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "docs")
REFERENCE  = os.path.join(SCRIPT_DIR, "reference.docx")
MERGED     = os.path.join(BRAIN_DIR, "_merged_strategy_report.md")
OUTPUT     = os.path.join(OUTPUT_DIR, "Muressons_Investment_Strategy_Comprehensive_Guide.docx")

SOURCES = [
    os.path.join(BRAIN_DIR, "investment_strategy_and_round_outcomes.md"),
    os.path.join(BRAIN_DIR, "investment_strategy_balance_sheet_impact.md"),
    os.path.join(BRAIN_DIR, "investment_strategy_share_price_impact.md"),
]

COVER = (
    "% Muressons Global Corporation\n"
    "% Investment Strategy and Valuation Guide\n"
    "% June 2026\n\n"
    "\\newpage\n\n"
    "# About This Document\n\n"
    "This document is a comprehensive reference for facilitators, players, and curriculum "
    "designers. It explains how every investment decision in the Muressons Global Corporation "
    "simulation flows through three interconnected layers:\n\n"
    "**Part I** covers Round Outcomes: how crisis decisions (A/B/C) and the five Strategic "
    "Pillar investments interact round by round, setting flags that cascade across the full "
    "10-round arc.\n\n"
    "**Part II** covers Balance Sheet Impact: how those decisions are recognised on the IFRS "
    "balance sheet including PPE capitalisation, environmental provisions, brand revaluation, "
    "goodwill impairment, covenant mechanics, and the equity bridge.\n\n"
    "**Part III** covers Share Price Impact: how every balance sheet and M_R movement "
    "translates into the terminal share price, including per-decision dollar values, "
    "pathway-specific modifiers, and the complete sensitivity matrix.\n\n"
    "Each Part can be read independently.\n\n"
    "\\newpage\n\n"
)

SEPARATORS = [
    None,
    "\n\n---\n\n\\newpage\n\n# PART II: BALANCE SHEET IMPACT\n\n---\n\n",
    "\n\n---\n\n\\newpage\n\n# PART III: SHARE PRICE IMPACT\n\n---\n\n",
]


def merge_sources():
    parts = [COVER]
    for i, src in enumerate(SOURCES):
        if not os.path.exists(src):
            print(f"  ERROR: Source not found: {src}")
            sys.exit(1)
        with open(src, encoding="utf-8") as f:
            content = f.read().strip()
        if SEPARATORS[i]:
            parts.append(SEPARATORS[i])
        if i > 0:
            lines = content.splitlines()
            if lines and lines[0].startswith("# "):
                content = "\n".join(lines[1:]).strip()
        parts.append(content)
    merged = "\n\n".join(parts)
    with open(MERGED, "w", encoding="utf-8") as f:
        f.write(merged)
    print(f"  Merged: {len(merged):,} chars -> {MERGED}")
    return MERGED


def build_docx(md_path, docx_path):
    pandoc_exe = shutil.which("pandoc")
    if not pandoc_exe:
        for c in [r"C:\Program Files\Pandoc\pandoc.exe",
                  r"C:\Users\Home\AppData\Local\Pandoc\pandoc.exe"]:
            if os.path.exists(c):
                pandoc_exe = c
                break
    if not pandoc_exe:
        print("  ERROR: pandoc not found. Run: winget install JohnMacFarlane.Pandoc")
        return False
    cmd = [pandoc_exe, md_path,
           "-f", "markdown+tex_math_dollars+smart", "-t", "docx",
           "--mathml", "--toc", "--toc-depth=3", "-o", docx_path]
    if os.path.exists(REFERENCE):
        cmd += ["--reference-doc", REFERENCE]
        print(f"  Brand style: {REFERENCE}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print("  ERROR:", result.stderr)
        return False
    if result.stderr.strip():
        print("  WARN:", result.stderr.strip())
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Muressons Investment Strategy Report Builder")
    print("=" * 60)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("\nMerging sources...")
    md = merge_sources()
    print("\nBuilding Word document...")
    ok = build_docx(md, OUTPUT)
    if ok:
        kb = round(os.path.getsize(OUTPUT) / 1024, 1)
        print(f"\n  SUCCESS: {OUTPUT} ({kb} KB)")
    else:
        sys.exit(1)
