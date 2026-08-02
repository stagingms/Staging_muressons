import os
import docx
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

def main():
    base_dir = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim"
    doc_path = os.path.join(base_dir, "docs", "Muressons_Facilitator_Manual_v10.docx")
    
    if not os.path.exists(doc_path):
        print(f"Error: {doc_path} not found.")
        return
        
    print(f"Loading {doc_path}...")
    doc = docx.Document(doc_path)
    
    # ── Find start and next heading ──────────────────────────────────────────
    p_start = None
    p_next_heading = None
    
    for p in doc.paragraphs:
        if p.text.strip() == "Appendix: Balance Sheet — Statement of Financial Position":
            p_start = p
            break
            
    if not p_start:
        print("Error: Heading 'Appendix: Balance Sheet — Statement of Financial Position' not found.")
        return
        
    found_start = False
    for p in doc.paragraphs:
        if p._element == p_start._element:
            found_start = True
            continue
        if found_start and p.style.name == "Heading 1":
            p_next_heading = p
            break
            
    if not p_next_heading:
        print("Warning: Next Heading 1 not found. Will delete till the end.")
        
    print("Found target section. Deleting legacy elements...")
    
    # ── Delete elements in between ───────────────────────────────────────────
    body = doc.element.body
    deleting = False
    to_remove = []
    
    for child in list(body):
        if child == p_start._element:
            deleting = True
            continue
        if p_next_heading and child == p_next_heading._element:
            deleting = False
            break
        if deleting:
            to_remove.append(child)
            
    for child in to_remove:
        body.remove(child)
        
    print(f"Removed {len(to_remove)} legacy elements. Inserting updated LaTeX-formatted content...")
    
    # Helper to insert paragraphs before p_next_heading
    def add_para_before(text, bold=False, italic=False, size=10.5, style=None):
        if p_next_heading:
            p = p_next_heading.insert_paragraph_before(style=style)
        else:
            p = doc.add_paragraph(style=style)
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.size = Pt(size)
        return p
        
    def add_formatted_math(formula):
        import re
        # Pre-process fractions: convert \frac{A}{B} to (A) / (B)
        while r"\frac" in formula:
            match = re.search(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", formula)
            if match:
                numerator, denominator = match.groups()
                formula = formula.replace(match.group(0), f"({numerator}) / ({denominator})")
            else:
                break
                
        # Clean up standard LaTeX constructs
        formula = re.sub(r"\\text\{([^{}]+)\}", r"\1", formula)
        formula = formula.replace(r"\times", " × ")
        formula = formula.replace(r"\sqrt", "√")
        formula = formula.replace(r"\max", "max")
        formula = formula.replace(r"\min", "min")
        formula = formula.replace(r"\left(", "(").replace(r"\right)", ")")
        formula = formula.replace(r"\%", "%")
        formula = formula.replace(r"\$", "$")
        formula = formula.replace(r"\\", "") # clean double backslashes
        formula = formula.strip("$ ") # clean leading/trailing dollar signs
        
        if p_next_heading:
            p = p_next_heading.insert_paragraph_before()
        else:
            p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        
        # Tokenize the formula
        pattern = re.compile(
            r"(_\{[A-Za-z0-9_ ]+\}|_[A-Za-z0-9]+|[A-Za-z]+|[0-9]+(?:\.[0-9]+)?%?|[+\-*/=()<>,√\$×−]|\s+)"
        )
        tokens = pattern.findall(formula)
        
        variables = {
            "PPE", "CAPEX", "ROU", "Inventory", "Brand", "Base", "Reputation", "SLO", "IP", 
            "Goodwill", "Revenue", "OPEX", "Debt", "Equity", "Liabilities", "Assets", 
            "EBITDA", "Cash", "WACC", "Obligation", "Accretion", "Tax", "Profit", 
            "DSO", "DPO", "Risk", "Exposure", "NCD", "Final", "Opening", "final", "opening",
            "allocated", "avg", "min", "max", "total", "net", "gross", "decomm", "interest", 
            "rate", "charge", "provision", "remediation", "events", "shares", "outstanding"
        }
        
        for token in tokens:
            if not token:
                continue
            run = p.add_run()
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
            
            if token.startswith("_"):
                sub_text = token[2:-1] if token.startswith("_{") else token[1:]
                run.text = sub_text
                run.font.subscript = True
                if sub_text in variables or sub_text.lower() in variables:
                    run.italic = True
            elif token in variables or token.lower() in variables:
                if token in ["min", "max", "avg"]:
                    run.italic = False
                    run.text = token
                else:
                    run.italic = True
                    run.text = token
            elif token == "*":
                run.text = " × "
            elif token == "-":
                run.text = " − "
            else:
                run.text = token
        return p
        
    def add_heading_before(text, level=2):
        if p_next_heading:
            h = p_next_heading.insert_paragraph_before(style=f"Heading {level}")
        else:
            h = doc.add_heading(text, level=level)
        run = h.add_run(text)
        colors = {2: (0x1D, 0x4E, 0xD8), 3: (0x78, 0x71, 0x6C)}
        c = colors.get(level, (0, 0, 0))
        run.font.color.rgb = RGBColor(*c)
        run.bold = True
        return h
        
    def add_bullet_before(text, bold_prefix=None):
        if p_next_heading:
            p = p_next_heading.insert_paragraph_before(style="List Bullet")
        else:
            p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Inches(0.3)
        if bold_prefix:
            r1 = p.add_run(bold_prefix + " ")
            r1.bold = True
            r1.font.size = Pt(10.5)
        run = p.add_run(text)
        run.font.size = Pt(10.5)
        return p
        
    def add_callout_before(text, label="ℹ️ Note", color=(0x05, 0x96, 0x69)):
        if p_next_heading:
            p = p_next_heading.insert_paragraph_before()
        else:
            p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.35)
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(f"{label}  {text}")
        r.italic = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(*color)
        return p
        
    def add_table_before(headers, rows, header_color="1D4ED8"):
        # We create the table and then insert its xml element
        table = doc.add_table(rows=1 + len(rows), cols=len(headers))
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        hdr = table.rows[0].cells
        for i, h in enumerate(headers):
            hdr[i].text = h
            set_cell_bg(hdr[i], header_color)
            for run in hdr[i].paragraphs[0].runs:
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.size = Pt(9.5)
                
        for ri, row in enumerate(rows):
            cells = table.rows[ri + 1].cells
            for ci, val in enumerate(row):
                cells[ci].text = str(val)
                for run in cells[ci].paragraphs[0].runs:
                    run.font.size = Pt(9.5)
                if ri % 2 == 0:
                    set_cell_bg(cells[ci], "F0FDF4")
                    
        # Add a spacer paragraph after table
        spacer = doc.add_paragraph()
        
        if p_next_heading:
            p_next_heading._element.addprevious(table._tbl)
            p_next_heading._element.addprevious(spacer._element)
        return table

    # ── Insert Updated Appendix Content ──────────────────────────────────────
    add_para_before(
        "This appendix provides facilitators with a complete reference to every line item, "
        "subtotal, ratio, and indicator displayed on the Muressons balance sheet (Statement "
        "of Financial Position). For each item, we explain what it represents in real-world "
        "corporate finance, the IFRS standard that governs it, how it is calculated in the "
        "simulation engine, and common misunderstandings that students may exhibit.",
        italic=True
    )
    
    add_para_before(
        "A balance sheet (formally: Statement of Financial Position under IFRS/IAS 1) is a "
        "snapshot of what a company owns (Assets), what it owes (Liabilities), and what is "
        "left over for shareholders (Equity) at a single point in time. The fundamental "
        "accounting identity is:"
    )
    
    add_formatted_math(r"$$Assets = Liabilities + Equity$$")
    
    add_para_before(
        "This identity must always hold. In the Muressons simulation, the balance sheet "
        "engine enforces this by deriving Retained Earnings as the residual figure after "
        "all asset and liability lines are independently updated each round."
    )
    
    # ── Section 1: Non-Current Assets ──
    add_heading_before("D1.1 Non-Current Assets (Tangible & Intangible)", level=2)
    
    add_para_before("1. Property, Plant & Equipment (PPE) [IAS 16]", bold=True)
    add_para_before(
        "PPE represents the capitalized physical infrastructure of the Business Units (BUs). In the simulation, "
        "when players allocate CAPEX, 60% is capitalized as PPE, while the remaining 40% is expensed as Opex. "
        "Straight-line depreciation is applied at 10% annually (5% per 6-month round). Depreciation in a given "
        "round is applied only to the opening PPE balance (prior to new CAPEX additions), per IAS 16 §55."
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{PPE}_{\text{final}} = \text{PPE}_{\text{opening}} + (\text{CAPEX}_{\text{allocated}} \times 0.60) - (\text{PPE}_{\text{opening}} \times 0.05)$$")
    
    add_para_before("2. Right-of-Use Assets (IFRS 16)", bold=True)
    add_para_before(
        "ROU Assets represent leased physical resources (e.g. office spaces, machinery). At initialization, "
        "it is seeded at 40% of revenue. It is amortized straight-line by 5% annually (2.5% per 6-month round)."
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{ROU}_{\text{final}} = \text{ROU}_{\text{opening}} \times (1 - 0.025)$$")
    
    add_para_before("3. Inventory [IAS 2]", bold=True)
    add_para_before(
        "Inventory represents stockpiled goods, raw materials, and finished products. In Muressons, inventory "
        "is dynamically recalculated each round based on a 60-day stock level model of total operating expenses "
        "(acting as a proxy for the cost of goods sold)."
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{Inventory} = \frac{\text{Total OPEX}}{365} \times 60$$")
    
    add_para_before("4. Brand Value [IAS 38]", bold=True)
    add_para_before(
        "Brand Value represents intangible corporate reputation. To prevent runaway compounding, the revaluation "
        "is calculated against a fixed brand base ($6.25M per BU, or $25.0M for a standard 4-BU group). It scales "
        "based on Group Reputation and the average Social License to Operate (SLO) score, subject to a hard floor of $1.0M."
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{Brand Value} = \text{Brand Base} \times \left(\frac{\text{Group Reputation}}{50}\right) \times \sqrt{\frac{\text{Average SLO}}{50}}$$")
    
    add_para_before("5. Intellectual Property (IP) [IAS 38]", bold=True)
    add_para_before(
        "Seeded at a flat $15.0M base plus $2.0M per BU ($23.0M for a standard 4-BU configuration). "
        "This remains flat unless impaired or increased by specific player decisions."
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{IP} = \$15.0\text{M} + (N_{\text{BUs}} \times \$2.0\text{M})$$")
    
    add_para_before("6. Goodwill [IAS 36]", bold=True)
    add_para_before(
        "Goodwill represents acquisition premiums, seeded at $2.5M per BU ($10.0M for 4 BUs). It is tested "
        "for impairment every 2 rounds (annual equivalent). Impairment is triggered if Group Reputation falls "
        "below 40 or EBITDA Margin falls below 10%, using a smooth continuous formula:"
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{Rep Impairment \%} = \max\left(0, \frac{40 - \text{Rep}}{200}\right)$$")
    add_formatted_math(r"$$\text{Margin Impairment \%} = \max\left(0, (0.10 - \text{EBITDA Margin}) \times 0.5\right)$$")
    add_formatted_math(r"$$\text{Total Impairment \%} = \min\left(0.30, \text{Rep Impairment \%} + \text{Margin Impairment \%}\right)$$")
    
    add_para_before("7. Non-GAAP ESG Capitals [IAS 38 / <IR> Framework]", bold=True)
    add_para_before(
        "Internally generated intangibles like community goodwill or employee trust cannot be recognized on a GAAP "
        "balance sheet under IAS 38. They are disclosed separately as off-balance sheet disclosures under the Integrated Reporting <IR> Framework:"
    )
    add_bullet_before("Social Licence Capital:")
    add_formatted_math(r"$$\text{Social Licence Capital} = \text{Average SLO} \times \$200,000$$")
    add_bullet_before("Reputation Capital:")
    add_formatted_math(r"$$\text{Reputation Capital} = \text{Group Reputation} \times \$300,000$$")
    
    # ── Section 2: Current Assets ──
    add_heading_before("D1.2 Current Assets", level=2)
    
    add_para_before("1. Cash & Equivalents", bold=True)
    add_para_before("Money in bank accounts, synchronized directly with the Corporate Treasury engine.")
    
    add_para_before("2. Trade Receivables [IFRS 9 / IFRS 15]", bold=True)
    add_para_before(
        "Outstanding customer payments, calculated via a Days Sales Outstanding (DSO) proxy that increases with Governance Risk."
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{DSO Factor} = \min\left(0.25, 0.12 + 0.001 \times \text{Average Gov Risk}\right)$$")
    add_formatted_math(r"$$\text{Trade Receivables} = \text{Total Revenue} \times \text{DSO Factor}$$")
    
    add_para_before("3. Prepayments", bold=True)
    add_para_before("Advance payments for services/insurance, seeded at a flat $250K per BU ($1.0M for 4 BUs).")
    
    # ── Section 3: Liabilities ──
    add_heading_before("D1.3 Liabilities (Non-Current & Current)", level=2)
    
    add_para_before("1. Revolving Credit Facility", bold=True)
    add_para_before("Long-term bank credit facility, seeded at $12.5M per BU ($50M for 4 BUs). Subject to covenant status.")
    
    add_para_before("2. Green Bonds Outstanding", bold=True)
    add_para_before("Debt issued to fund environmental projects, initialized at $0.0M and incremented by player decisions.")
    
    add_para_before("3. Environmental Provisions [IAS 37]", bold=True)
    add_para_before(
        "Provision for future cleanup costs. Driven by Natural Capital Debt (NCD) and active remediation events, "
        "subject to an irreducible floor of $1.0M. Unlike a permanent ratchet, provisions can decrease when NCD drops (IAS 37 §59)."
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{Environmental Provision} = \max\left(\$1.0\text{M}, (\text{Average NCD} \times 5000) + (\text{Active Remediation Events} \times 2,000,000)\right)$$")
    
    add_para_before("4. Decommissioning Obligations [IAS 37 / IFRIC 1]", bold=True)
    add_para_before(
        "Expected asset dismantlement costs, seeded at $750K per BU ($3.0M for 4 BUs). It accretes at a 3% annual "
        "discount rate (1.5% per 6-month round), with the accretion recognized as interest expense."
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{Accretion Charge} = \text{Obligation}_{\text{opening}} \times 0.015$$")
    add_formatted_math(r"$$\text{Obligation}_{\text{final}} = \text{Obligation}_{\text{opening}} + \text{Accretion Charge}$$")
    
    add_para_before("5. Lease Liabilities (IFRS 16)", bold=True)
    add_para_before("Outstanding lease obligations, seeded at 35% of total revenue. It amortizes by 5% annually (2.5% per 6-month round).")
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{Lease Liability}_{\text{final}} = \text{Lease Liability}_{\text{opening}} \times 0.975$$")
    
    add_para_before("6. Trade Payables", bold=True)
    add_para_before("Owed supplier payments, scaled by operating expenses and Days Payable Outstanding (DPO).")
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{DPO Factor} = \min\left(0.18, 0.10 + 0.0005 \times \text{Average Gov Risk}\right)$$")
    add_formatted_math(r"$$\text{Trade Payables} = \text{Total OPEX} \times \text{DPO Factor}$$")
    
    add_para_before("7. Tax Provisions [IAS 12]", bold=True)
    add_para_before("Taxes owed on current-round profits (prepayments modeling).")
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{Tax Provision} = \max\left(0, \text{Gross Profit} \times 0.25 \times 0.20\right)$$")
    
    # ── Section 4: Equity ──
    add_heading_before("D1.4 Shareholders' Equity", level=2)
    
    add_para_before("1. Share Capital", bold=True)
    add_para_before("Common stock invested at initialization, seeded at $7.5M per BU ($30.0M for 4 BUs).")
    
    add_para_before("2. Other Reserves", bold=True)
    add_para_before("Capital and hedging reserves, seeded at $1.25M per BU ($5.0M for 4 BUs).")
    
    add_para_before("3. Retained Earnings", bold=True)
    add_para_before(
        "Derived as the closing residual balance to enforce the accounting identity $A = L + E$. Profitability is "
        "tracked via Net Income on the accrual-based Income Statement, with dividends deducted separately."
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{Retained Earnings} = \text{Net Assets} - \text{Share Capital} - \text{Other Reserves}$$")
    add_formatted_math(r"$$\text{Net Income} = \text{Gross Profit} - \text{Interest Expense} - \text{Depreciation} - \text{Expensed CAPEX} - \text{Tax Charge}$$")
    
    # ── Section 5: Key Ratios ──
    add_heading_before("D1.5 Key Ratios & Covenants", level=2)
    
    add_para_before("1. Debt / Equity Ratio", bold=True)
    add_formatted_math(r"$$\text{Debt / Equity} = \frac{\text{Total Liabilities}}{\text{Total Equity}}$$")
    
    add_para_before("2. Net Debt / EBITDA Ratio", bold=True)
    add_para_before(
        "Measures leverage. Banks set a standard breach trigger at 3.5x. Under the simulation's rules, "
        "EBITDA adds back depreciation (D&A) to calculate true earnings, and WACC > 8% tightens the trigger by -0.25x per 1% excess."
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{Total Debt} = \text{Revolving Credit} + \text{Green Bonds} + \text{Short-Term Debt}$$")
    add_formatted_math(r"$$\text{Net Debt} = \text{Total Debt} - \text{Cash}$$")
    add_formatted_math(r"$$\text{EBITDA} = \text{Gross Profit} + \text{Depreciation}$$")
    add_formatted_math(r"$$\text{Net Debt / EBITDA} = \frac{\text{Net Debt}}{\text{EBITDA}}$$")
    
    add_para_before("3. Stranded Asset Exposure", bold=True)
    add_para_before(
        "Represents the value of PPE at risk from carbon transition and climate pathways (Carbon Tracker methodology)."
    )
    add_para_before("Formula (LaTeX):")
    add_formatted_math(r"$$\text{CI Risk} = \min\left(0.5, \frac{\text{Carbon Intensity Avg}}{200}\right)$$")
    add_formatted_math(r"$$\text{Total Risk} = \min(0.80, \text{CI Risk} + \text{Pathway Risk} + \text{Tipping Risk})$$")
    add_formatted_math(r"$$\text{Stranded Exposure} = \text{PPE} \times \text{Total Risk}$$")
    
    # ── Section 6: Misconceptions ──
    add_heading_before("D1.6 Common Student Misconceptions & Facilitator Teaching Moments", level=2)
    
    add_table_before(
        ["Misconception", "Correct Understanding", "Suggested Response / Teachable Moment"],
        [
            ["\"Negative cash means we're bankrupt.\"",
             "Negative cash represents a bank overdraft. Insolvency depends on whether total liabilities exceed total assets (i.e. negative equity).",
             "\"Is the company insolvent because of the cash, or because of the accumulated losses? What does equity tell you? Let's check the Debt/Equity ratio.\""],
             
            ["\"We should maximize Total Assets at all costs.\"",
             "Asset growth is only valuable if it generates returns above cost of capital. Accumulating unproductive assets destroys value.",
             "\"What is the Return on Assets (ROA)? Is growing the asset base actually creating shareholder value? What is the impact of WACC?\""],
             
            ["\"Goodwill is a permanent asset.\"",
             "Goodwill must be tested for impairment annually. Low reputation or poor margins trigger write-downs under IAS 36.",
             "\"What happens to goodwill when the company's reputation drops below 40? Let's trace the smooth impairment formula in the math engine.\""],
             
            ["\"The non-GAAP ESG items should be on our Balance Sheet.\"",
             "IAS 38 prohibits capitalizing internally generated intangibles. The <IR> Framework advocacy is a scholarly debate, not current standard IFRS.",
             "\"Let's activate the Scholarly Toggle in God Mode. What changes on the balance sheet? Why does the standard restrict this?\""]
        ]
    )
    
    # ── Section 7: Accounting Walkthrough ──
    add_heading_before("D1.7 Accounting Equation Worked Walkthrough (For a 4-BU group)", level=2)
    
    add_para_before(
        "For a standard 4-BU group, the initial assets and liabilities are scaled. "
        "For example, when a group finishes Round 2, their balance sheet might look like this:"
    )
    
    add_bullet_before("Tangible Assets: PPE ($25.0M) + ROU ($19.0M) + Inventory ($6.5M) = $50.5M")
    add_bullet_before("Intangible Assets: Brand ($25.1M) + IP ($23.0M) + Goodwill ($10.0M) = $58.1M")
    add_bullet_before("Current Assets: Cash ($56.4M) + Trade Receivables ($6.2M) + Prepayments ($1.0M) = $63.7M")
    add_formatted_math(r"$$\text{TOTAL ASSETS} = 50.5\text{M} + 58.1\text{M} + 63.7\text{M} = 172.3\text{M}$$")
    
    add_bullet_before("Non-Current Liabilities: Revolving Credit ($50.0M) + Environmental ($1.0M) + Decommissioning ($3.0M) + Lease ($16.6M) = $70.7M")
    add_bullet_before("Current Liabilities: Trade Payables ($4.1M) + Tax Provision ($0.445M) = $4.6M")
    add_formatted_math(r"$$\text{TOTAL LIABILITIES} = 70.7\text{M} + 4.6\text{M} = 75.3\text{M}$$")
    
    add_para_before("Using the accounting equation:")
    add_formatted_math(r"$$\text{Net Assets} = \text{Total Assets} - \text{Total Liabilities} = 172.3\text{M} - 75.3\text{M} = 97.1\text{M}$$")
    add_formatted_math(r"$$\text{Total Equity} = \text{Share Capital (\$30.0M)} + \text{Other Reserves (\$5.0M)} + \text{Retained Earnings (\$62.1M)} = 97.1\text{M}$$")
    add_formatted_math(r"$$\text{Verification: Net Assets} = \text{Total Equity} \implies 97.1\text{M} = 97.1\text{M} \quad \checkmark$$")

    print(f"Saving updated manual to {doc_path}...")
    doc.save(doc_path)
    print("SUCCESS: Facilitator Manual updated successfully!")

if __name__ == "__main__":
    main()
