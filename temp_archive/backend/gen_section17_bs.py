"""
Generate Section 17 — Balance Sheet Engine
as a Word document to append to the Muressons Facilitator Manual.
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def add_heading(doc, text, level=1, color='#1e3a5f'):
    h = doc.add_heading(text, level)
    r,g,b = hex_to_rgb(color)
    for run in h.runs:
        run.font.color.rgb = RGBColor(r,g,b)
        run.font.bold = True
    return h

def add_para(doc, text, indent=0, bold=False, italic=False, size=10, color=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        r,g,b = hex_to_rgb(color)
        run.font.color.rgb = RGBColor(r,g,b)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    return p

def add_code_block(doc, lines):
    """Add a monospace code block."""
    for line in lines:
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.name = 'Courier New'
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(30, 30, 30)
        p.paragraph_format.left_indent = Cm(1)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        # Light grey background via paragraph border
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), 'F0F4F8')
        pPr.append(shd)

def add_table(doc, headers, rows, col_widths=None, header_color='#1e3a5f'):
    table = doc.add_table(rows=1+len(rows), cols=len(headers))
    table.style = 'Table Grid'
    # Header row
    hdr_row = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.text = h
        run = cell.paragraphs[0].runs[0]
        run.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(255,255,255)
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        r,g,b = hex_to_rgb(header_color)
        shd.set(qn('w:fill'), f'{r:02X}{g:02X}{b:02X}')
        tcPr.append(shd)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Data rows
    for ri, row_data in enumerate(rows):
        row = table.rows[ri+1]
        fill = 'EBF1F8' if ri % 2 == 0 else 'FFFFFF'
        for ci, val in enumerate(row_data):
            cell = row.cells[ci]
            cell.text = str(val)
            cell.paragraphs[0].runs[0].font.size = Pt(9)
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            shd = OxmlElement('w:shd')
            shd.set(qn('w:val'), 'clear')
            shd.set(qn('w:color'), 'auto')
            shd.set(qn('w:fill'), fill)
            tcPr.append(shd)
    if col_widths:
        for ci, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[ci].width = Cm(w)
    doc.add_paragraph()
    return table

def add_bs_line(doc, label, amount, bold=False, color=None, indent=1):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(indent)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.space_before = Pt(1)
    run1 = p.add_run(label)
    run1.font.size = Pt(9)
    run1.bold = bold
    if color:
        r,g,b = hex_to_rgb(color)
        run1.font.color.rgb = RGBColor(r,g,b)
    # Tab-aligned amount
    tab = p.add_run('\t')
    tab.font.size = Pt(9)
    run2 = p.add_run(f'  {amount}')
    run2.font.size = Pt(9)
    run2.bold = bold
    run2.font.name = 'Courier New'
    if color:
        r,g,b = hex_to_rgb(color)
        run2.font.color.rgb = RGBColor(r,g,b)
    return p

def add_separator(doc, color='#1e3a5f'):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.space_before = Pt(2)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    r,g,b = hex_to_rgb(color)
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), f'{r:02X}{g:02X}{b:02X}')
    pBdr.append(bottom)
    pPr.append(pBdr)

def fmt(n): return f'${n:>14,.0f}'

# ──────────────────────────────────────────────────────────────
doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

# Normal style
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(10)

# ── TITLE ─────────────────────────────────────────────────────
title = doc.add_heading('Section 17: The Balance Sheet Engine (SE-6)', 0)
for run in title.runs:
    run.font.color.rgb = RGBColor(0x1e,0x3a,0x5f)
    run.font.size = Pt(18)
add_para(doc, 'Muressons Global Corporation — Facilitator Reference Manual', size=11, italic=True, color='#64748b')
add_separator(doc, '#1e3a5f')
doc.add_paragraph()

# ── 17.1 PURPOSE ─────────────────────────────────────────────
add_heading(doc, '17.1  Purpose and Theory Base', 2, '#1e3a5f')
add_para(doc, 'The Balance Sheet Engine (SE-6) provides participants with an IFRS-compliant Statement of Financial Position that updates every round alongside the treasury (cash-flow) model. It teaches three things simultaneously:')
for item in [
    '1. The accounting identity — Assets = Liabilities + Equity — and how every decision that changes assets or liabilities must be reflected in equity.',
    '2. ESG–financial integration — how carbon intensity, governance risk, social licence, and reputation translate into measurable financial risk (stranded assets, covenant tightening, brand value erosion, goodwill impairment).',
    '3. Lender dynamics — how debt covenants work in practice, including the real-money consequences of ESG-adjusted cost of capital on credit terms.',
]:
    add_para(doc, item, indent=0.8)

doc.add_paragraph()
add_heading(doc, 'Standards Applied', 3, '#2563eb')
add_table(doc,
    ['Standard', 'Application in SE-6'],
    [
        ['IAS 1 — Statement of Financial Position', 'Overall structure: Non-current assets, Current assets, NCL, CL, Equity'],
        ['IAS 16 — Property, Plant & Equipment', 'CAPEX capitalisation (60%), straight-line depreciation (10% p.a., 5% per round)'],
        ['IAS 36 — Impairment of Assets', 'Annual goodwill impairment test (every 2 rounds), dual trigger: reputation + EBITDA margin'],
        ['IAS 37 — Provisions', 'Environmental provisions (reversible per §59), decommissioning accretion'],
        ['IAS 38 — Intangible Assets', 'Social licence & reputation NOT on GAAP balance sheet (internally generated)'],
        ['IFRS 16 — Leases', 'Right-of-Use assets & lease liabilities; 2.5%/round amortisation'],
        ['IFRIC 1 — Decommissioning Changes', 'Accretion of decommissioning provision at 3% p.a. discount rate'],
        ['<IR> Framework', 'Six Capitals: social/reputation capitals as non-GAAP supplementary ESG disclosure'],
        ['Carbon Tracker Initiative', 'Stranded asset methodology — CI-based % of PPE at climate transition risk'],
    ],
    col_widths=[6.5, 9.5]
)

# ── 17.2 ARCHITECTURE ─────────────────────────────────────────
add_heading(doc, '17.2  Architecture and Processing Flow', 2, '#1e3a5f')
add_para(doc, 'The engine is a pure-function module (balance_sheet.py) called once per round from run_new_engines() in round_logic.py after all player decisions are processed. It operates in 9 sequential steps:')
doc.add_paragraph()

steps = [
    ('Step 0', 'Extract Inputs', 'Revenue, OPEX, governance risk, treasury synced from global state'),
    ('Step 1', 'CAPEX Capitalisation (IAS 16)', '60% of player investment → PPE; 40% expensed to P&L'),
    ('Step 2', 'Depreciation — PPE + ROU', 'PPE: 5%/round on opening balance; ROU: 2.5%/round (IFRS 16)'),
    ('Step 3', 'Working Capital Update', 'Inventory (60-day OPEX model), DSO receivables, DPO payables, tax provision'),
    ('Step 4', 'Intangible Revaluation', 'Brand = Base × (Rep/50) × √(SLO/50); Goodwill IAS 36 test (even rounds)'),
    ('Step 5', 'Stranded Asset Exposure', 'Carbon Tracker: CI risk + pathway risk + tipping risk × PPE'),
    ('Step 6', 'Liability Updates', 'Env provisions (IAS 37 §59 reversals), lease amortisation, decommissioning accretion'),
    ('Step 7', 'Income Statement', 'Net income = Gross Profit − Depreciation − CAPEX expensed − Interest − Tax'),
    ('Step 8', 'Close A = L + E', 'RE derived as Net Assets − Share Capital − Other Reserves (closing identity)'),
    ('Step 9', 'Covenant Check', 'ND/EBITDA vs ESG-WACC-adjusted trigger; treasury surcharge for breach'),
]
add_table(doc,
    ['Step', 'Name', 'What It Does'],
    steps,
    col_widths=[1.5, 5.0, 9.5]
)

doc.add_paragraph()
add_para(doc, 'Important: The Treasury (cash-flow) engine in engine.py remains the primary model. The balance sheet is a parallel accounting layer that reads corporate_treasury as its cash figure each round. Cash on the balance sheet always equals the corporate treasury exactly.', italic=True, color='#475569')

# ── 17.3 ROUND 0 ─────────────────────────────────────────────
doc.add_page_break()
add_heading(doc, '17.3  Round 0 — Opening Balance Sheet', 2, '#1e3a5f')
add_para(doc, 'All fixed monetary items scale linearly with the number of Business Units (n_BUs). The standard 4-BU configuration is used throughout this section.')

doc.add_paragraph()
add_heading(doc, 'Scale-with-BU Parameters', 3, '#2563eb')
add_table(doc,
    ['Balance Sheet Item', 'Per-BU Amount', '4-BU Total'],
    [
        ['Revolving Credit Facility', '$12,500,000', '$50,000,000'],
        ['Brand Value Base (stable reference)', '$6,250,000', '$25,000,000'],
        ['Goodwill', '$2,500,000', '$10,000,000'],
        ['Environmental Provisions (seed)', '$1,250,000', '$5,000,000'],
        ['Decommissioning Obligations (seed)', '$750,000', '$3,000,000'],
        ['Share Capital', '$7,500,000', '$30,000,000'],
        ['Other Reserves', '$1,250,000', '$5,000,000'],
        ['Prepayments', '$250,000', '$1,000,000'],
        ['Intellectual Property', '$15M base + $2M/BU', '$23,000,000'],
    ],
    col_widths=[7.5, 4.0, 4.5]
)

doc.add_paragraph()
add_heading(doc, 'Revenue- and OPEX-Driven Items (4-BU: Rev $53.5M, OPEX $34.3M)', 3, '#2563eb')
add_table(doc,
    ['Item', 'Formula', 'Amount'],
    [
        ['Inventory', '(Total OPEX ÷ 365) × 60 days', '$5,638,356'],
        ['Right-of-Use Assets', 'Total Revenue × 40%', '$21,400,000'],
        ['Trade Receivables', 'Total Revenue × 12% (DSO ~44 days)', '$6,420,000'],
        ['Lease Liabilities', 'Total Revenue × 35%', '$18,725,000'],
        ['Trade Payables', 'Total Revenue × 12%', '$6,420,000'],
    ],
    col_widths=[5.0, 6.0, 5.0]
)

doc.add_paragraph()
add_heading(doc, 'PPE Closing Formula (FIX-1: Option B)', 3, '#2563eb')
add_para(doc, 'PPE is derived algebraically rather than set as an arbitrary revenue multiple. This guarantees A = L + E from Round 1 with zero residual imbalance:')
add_code_block(doc, [
    'Non-PPE Assets = Inventory + ROU Assets + Brand + IP + Goodwill + Trade Receivables + Prepayments',
    '',
    'PPE = Total Liabilities + Fixed Equity − Non-PPE Assets',
    '',
    'Where: Fixed Equity = Share Capital + Other Reserves',
    '',
    'Retained Earnings = Total Assets − Total Liabilities − Fixed Equity',
    '                  = 0 at Round 0 (no earnings recognised yet)',
])

# ── 17.4 COMPLETE SAMPLE CALCULATION ─────────────────────────
doc.add_page_break()
add_heading(doc, '17.4  Complete Sample Calculation — Round 0 Opening', 2, '#1e3a5f')

add_heading(doc, 'Business Unit Inputs (Standard 4-BU Configuration)', 3, '#2563eb')
add_table(doc,
    ['Business Unit', 'Revenue', 'OPEX', 'SLO', 'Gov Risk', 'Carbon Intensity'],
    [
        ['Pharma', '$18,000,000', '$11,500,000', '55', '15', '45'],
        ['Electronics', '$16,500,000', '$10,800,000', '48', '20', '72'],
        ['Consumer Goods', '$10,500,000', '$7,800,000', '52', '10', '38'],
        ['Software', '$8,500,000', '$4,200,000', '60', '8', '28'],
        ['TOTAL / AVG', '$53,500,000', '$34,300,000', '53.75', '13.25', '45.75'],
    ],
    col_widths=[3.5, 3.0, 3.0, 1.5, 2.0, 3.0]
)

doc.add_paragraph()
add_heading(doc, 'Asset Derivation', 3, '#2563eb')
add_code_block(doc, [
    'Inventory        = ($34,300,000 ÷ 365) × 60 days                 =  $5,638,356',
    'ROU Assets       = $53,500,000 × 40%                             = $21,400,000',
    'Brand Value      = $6,250,000 × 4 BUs                            = $25,000,000',
    'Intellectual P.  = $15,000,000 + (4 × $2,000,000)                = $23,000,000',
    'Goodwill         = $2,500,000 × 4 BUs                            = $10,000,000',
    'Trade Receivables= $53,500,000 × 12%                             =  $6,420,000',
    'Prepayments      = $250,000 × 4 BUs                              =  $1,000,000',
    '─────────────────────────────────────────────────────────────────────────────',
    'Non-PPE Total                                                     = $92,458,356',
])
doc.add_paragraph()
add_code_block(doc, [
    'Revolving Credit = $12,500,000 × 4 BUs                           = $50,000,000',
    'Env. Provisions  = $1,250,000 × 4 BUs                            =  $5,000,000',
    'Decommissioning  = $750,000 × 4 BUs                              =  $3,000,000',
    'Lease Liabilities= $53,500,000 × 35%                             = $18,725,000',
    'Trade Payables   = $53,500,000 × 12%                             =  $6,420,000',
    'Tax Provisions   = $0 (no P&L recognised at opening)             =          $0',
    '─────────────────────────────────────────────────────────────────────────────',
    'Total Liabilities                                                 = $83,145,000',
    '',
    'Share Capital    = $7,500,000 × 4 BUs                            = $30,000,000',
    'Other Reserves   = $1,250,000 × 4 BUs                            =  $5,000,000',
    'Fixed Equity                                                      = $35,000,000',
    '',
    'PPE = $83,145,000 + $35,000,000 − $92,458,356                    = $25,686,644',
    '',
    'Total Assets = $92,458,356 + $25,686,644                         = $118,145,000',
    'Retained Earnings = $118,145,000 − $83,145,000 − $35,000,000     =           $0',
    '',
    'CHECK:  A = $118,145,000   L+E = $83,145,000 + $35,000,000 = $118,145,000  ✓',
])

# ── ROUND 1 SAMPLE ─────────────────────────────────────────────
doc.add_page_break()
add_heading(doc, '17.5  Complete Sample Calculation — Round 1 First Tick', 2, '#1e3a5f')

add_para(doc, 'Scenario: Players invest $5,000,000 in CAPEX and declare $2,000,000 in dividends. Corporate treasury is $47,000,000. Group Reputation = 50. No ecological damage (NCD = 0).')
doc.add_paragraph()

# Step 1
add_heading(doc, 'Step 1: CAPEX Capitalisation (IAS 16)', 3, '#2563eb')
add_para(doc, 'IAS 16 §7: 60% of player CAPEX investment is capitalised as PPE (creates long-term productive capacity). 40% is expensed immediately (operational improvements, maintenance, consultancy).', italic=True)
add_code_block(doc, [
    'Total CAPEX Invested                             =  $5,000,000',
    'Capitalisation Rate                              =       60.0%',
    'Amount Capitalised → added to PPE               =  $3,000,000',
    'Amount Expensed → deducted in P&L (Step 7)      =  $2,000,000',
    '',
    'PPE after adding new CAPEX (before depreciation) = $28,686,644',
    '   = Opening PPE $25,686,644 + Capitalised $3,000,000',
    '',
    'IAS 16 §55 NOTE: Depreciation in Step 2 applies only to the',
    'opening balance ($25,686,644). New CAPEX starts depreciating',
    'from Round 2 (asset "available for use" at end of this round).',
])
doc.add_paragraph()

# Step 2
add_heading(doc, 'Step 2: Straight-Line Depreciation (IAS 16 + IFRS 16)', 3, '#2563eb')
add_code_block(doc, [
    'PPE:  Opening balance (pre-CAPEX)   = $25,686,644',
    '      Annual depreciation rate      =       10.0%  (10-year industrial life)',
    '      Period rate (6 months)        =        5.0%',
    '      PPE Depreciation charge       =  $1,284,332',
    '      PPE closing = $28,686,644 − $1,284,332      = $27,402,312',
    '',
    'ROU:  Opening balance               = $21,400,000',
    '      Annual depreciation rate      =        5.0%  (20-year property lease)',
    '      Period rate (6 months)        =        2.5%',
    '      ROU Depreciation charge       =    $535,000',
    '      ROU closing = $21,400,000 − $535,000         = $20,865,000',
    '',
    'TOTAL DEPRECIATION CHARGE                          =  $1,819,332',
])
doc.add_paragraph()

# Step 3
add_heading(doc, 'Step 3: Working Capital Update', 3, '#2563eb')
add_code_block(doc, [
    'Avg Governance Risk = (15+20+10+8) ÷ 4                 = 13.25',
    '',
    'DSO Factor = 0.12 + (0.001 × 13.25)                    = 0.1333',
    '  → Higher governance risk = slower collections = more receivables',
    'DPO Factor = 0.10 + (0.0005 × 13.25)                   = 0.1066',
    '  → Higher governance risk = longer payment terms to suppliers',
    '',
    'Inventory  = ($34,300,000 ÷ 365) × 60 days             =  $5,638,356',
    'Trade Rec. = $53,500,000 × 0.1333                       =  $7,128,875',
    'Trade Pay. = $34,300,000 × 0.1066                       =  $3,657,238',
    'Tax Prov.  = $19,200,000 (GP) × 25% × 20%              =    $960,000',
    '             (20% = quarterly prepayment portion)',
])
doc.add_paragraph()

# Step 4
add_heading(doc, 'Step 4: Intangible Asset Revaluation', 3, '#2563eb')
add_para(doc, 'Brand Value Formula (FIX-2): Brand = Brand_Base × (Reputation ÷ 50) × √(Avg_SLO ÷ 50)', bold=True)
add_para(doc, 'The brand is ALWAYS revalued against the stable Round 0 base ($25,000,000), not the prior-period value. This prevents exponential compounding where a good round inflates the next round\'s starting point.', italic=True)
add_code_block(doc, [
    'Brand Base (fixed, never changes)    = $25,000,000',
    'Group Reputation                     = 50',
    'Rep Factor = 50 ÷ 50                 = 1.0000',
    '',
    'Avg SLO = (55+48+52+60) ÷ 4         = 53.75',
    'SLO Factor = √(53.75 ÷ 50)          = √1.075 = 1.0368',
    '',
    'Brand Value = $25,000,000 × 1.0000 × 1.0368 = $25,920,552',
    '',
    'Goodwill Impairment (IAS 36):        Round 1 is ODD → no test this round',
    '                                     Test runs at Rounds 2, 4, 6, 8, 10',
    '',
    '[Non-GAAP] Social Licence Capital = 53.75 × $200,000 = $10,750,000',
    '[Non-GAAP] Reputation Capital     = 50 × $300,000    = $15,000,000',
    '  ↑ EXCLUDED from Total Assets per IAS 38',
])
doc.add_paragraph()

# Step 5
add_heading(doc, 'Step 5: Stranded Asset Exposure (Carbon Tracker Methodology)', 3, '#2563eb')
add_code_block(doc, [
    'Avg Carbon Intensity = (45+72+38+28) ÷ 4 = 45.75',
    '',
    'CI Risk   = min(50%, 45.75 ÷ 200)         = 22.9%',
    'Pathway   = Activist Ultimatum (default)   = 10.0%',
    'Tipping   = None (no tipping point yet)    =  0.0%',
    '────────────────────────────────────────────────────',
    'Total Risk = min(80%, 22.9%+10.0%+0.0%)   = 32.9%  → HIGH (>25%)',
    '',
    'Stranded Exposure = $27,402,312 × 32.9%   = $9,008,510',
    '  (32.9% of PPE is at climate transition risk)',
])
doc.add_paragraph()

# Step 6
add_heading(doc, 'Step 6: Liability Updates', 3, '#2563eb')
add_code_block(doc, [
    'Environmental Provisions (IAS 37 §59 reversal):',
    '  NCD avg = 0  →  NCD provision = 0 × $5,000 = $0',
    '  Event provision = 0 events × $2,000,000    = $0',
    '  New provision = max($1,000,000 floor, $0)  = $1,000,000',
    '  CHANGE: $5,000,000 → $1,000,000 (REVERSAL of $4,000,000)',
    '  (IAS 37 §59: reverse when obligating event no longer exists)',
    '',
    'Lease Liabilities (IFRS 16):',
    '  $18,725,000 × (1 − 2.5%) = $18,725,000 × 0.975 = $18,256,875',
    '',
    'Decommissioning Accretion (IFRIC 1):',
    '  Annual discount rate = 3.0%;  Period rate = 1.5%',
    '  Accretion = $3,000,000 × 1.5% = $45,000',
    '  Closing Decommissioning = $3,000,000 + $45,000 = $3,045,000',
    '  ($45,000 added to interest expense in Step 7)',
])
doc.add_paragraph()

# Step 7
add_heading(doc, 'Step 7: Income Statement', 3, '#2563eb')
add_para(doc, 'FIX-3: Dividends are an equity distribution, NOT a P&L expense. Net Income is the earnings available to shareholders; dividends reduce retained earnings separately.', italic=True)
add_code_block(doc, [
    'Revenue                                       $53,500,000',
    'Less OPEX                                    ($34,300,000)',
    '                                             ─────────────',
    'Gross Profit                                  $19,200,000',
    '',
    'Less:  Depreciation — PPE + ROU              ($ 1,819,332)',
    'Less:  CAPEX Expensed (40% of $5,000,000)    ($ 2,000,000)',
    'Less:  Interest Expense*                     ($ 1,250,000)',
    '         * = $50,000,000 debt × 5.0% WACC ÷ 2',
    'Less:  Decommissioning Accretion             ($    45,000)',
    '                                             ─────────────',
    'Taxable Income                                $14,085,668',
    '',
    'Less:  Corporation Tax (25%)                 ($ 3,521,417)',
    '                                             ─────────────',
    'NET INCOME                                    $10,564,251',
    '',
    'Dividends declared (equity distribution):    ($ 2,000,000)',
    '  → Noted for performance scoring; does not directly reduce',
    '     retained earnings (RE is derived as closing figure in Step 8)',
])
doc.add_paragraph()

# Step 8
add_heading(doc, 'Step 8: Balance Sheet Totals — Closing A = L + E Identity', 3, '#2563eb')
add_code_block(doc, [
    'Total Tangible Assets  = $27,402,312 + $5,638,356 + $20,865,000  = $53,905,668',
    'Total Intangible Assets= $25,920,552 + $23,000,000 + $10,000,000 = $58,920,552',
    'Total Current Assets   = $47,000,000 + $7,128,875 + $1,000,000   = $55,128,875',
    '─────────────────────────────────────────────────────────────────────────────',
    'TOTAL ASSETS           = $53,905,668 + $58,920,552 + $55,128,875 = $167,955,094',
    '',
    'Total NCL              = $72,301,875',
    'Total CL               =  $4,617,238',
    'TOTAL LIABILITIES      = $76,919,112',
    '',
    'Net Assets = $167,955,094 − $76,919,112                          = $91,035,982',
    '',
    'Retained Earnings = Net Assets − Share Capital − Other Reserves',
    '                  = $91,035,982 − $30,000,000 − $5,000,000',
    '                  = $56,035,982',
    '',
    'TOTAL EQUITY = $30,000,000 + $56,035,982 + $5,000,000            = $91,035,982',
    '',
    'CHECK:  $167,955,094  =  $76,919,112 + $91,035,982  ✓  (diff: $0.00)',
])
doc.add_paragraph()

# Round 1 Final BS
add_heading(doc, 'Round 1 — Final Statement of Financial Position', 3, '#1e3a5f')
add_table(doc,
    ['Category', 'Line Item', 'Amount'],
    [
        ['Tangible Assets', 'Property, Plant & Equipment', '$27,402,312'],
        ['', 'Right-of-Use Assets (IFRS 16)', '$20,865,000'],
        ['', 'Inventory', '$5,638,356'],
        ['', 'TOTAL TANGIBLE', '$53,905,668'],
        ['Intangible Assets', 'Brand Value', '$25,920,552'],
        ['', 'Intellectual Property', '$23,000,000'],
        ['', 'Goodwill', '$10,000,000'],
        ['', 'TOTAL INTANGIBLE', '$58,920,552'],
        ['Current Assets', 'Cash & Equivalents (= Treasury)', '$47,000,000'],
        ['', 'Trade Receivables', '$7,128,875'],
        ['', 'Prepayments', '$1,000,000'],
        ['', 'TOTAL CURRENT', '$55,128,875'],
        ['', 'TOTAL ASSETS ✓', '$167,955,094'],
        ['Non-Current Liabilities', 'Revolving Credit Facility', '$50,000,000'],
        ['', 'Environmental Provisions', '$1,000,000'],
        ['', 'Decommissioning Obligations', '$3,045,000'],
        ['', 'Lease Liabilities (IFRS 16)', '$18,256,875'],
        ['', 'TOTAL NCL', '$72,301,875'],
        ['Current Liabilities', 'Trade Payables', '$3,657,238'],
        ['', 'Tax Provisions', '$960,000'],
        ['', 'TOTAL CL', '$4,617,238'],
        ['', 'TOTAL LIABILITIES', '$76,919,112'],
        ['Equity', 'Share Capital', '$30,000,000'],
        ['', 'Retained Earnings (closing identity)', '$56,035,982'],
        ['', 'Other Reserves', '$5,000,000'],
        ['', 'TOTAL EQUITY ✓', '$91,035,982'],
        ['CHECK', 'TOTAL L + E ✓', '$167,955,094'],
    ],
    col_widths=[4.5, 6.0, 5.5]
)

doc.add_paragraph()
add_heading(doc, 'Step 9: Covenant Check', 3, '#2563eb')
add_code_block(doc, [
    'True EBITDA = Gross Profit + Total Depreciation',
    '           = $19,200,000 + $1,819,332              = $21,019,332',
    '',
    'Total Financial Debt = $50,000,000 (revolving credit)',
    'Cash                 = $47,000,000',
    'Net Debt             = $50,000,000 − $47,000,000   =  $3,000,000',
    '',
    'Net Debt / EBITDA = $3,000,000 ÷ $21,019,332       = 0.14×',
    '',
    'ESG-WACC            = 5.0%  (no ESG stress)',
    'WACC excess over 8% = 0%    → no covenant tightening',
    'Covenant Trigger    = 3.50×  (base trigger)',
    '',
    'Covenant Status: GREEN  (0.14× vs 3.50× trigger)',
    'Debt / Equity     = $76,919,112 ÷ $91,035,982 = 0.84×',
    '',
    'Non-GAAP ESG Capitals (excluded from total assets):',
    '  Social Licence Capital = 53.75 × $200,000 = $10,750,000',
    '  Reputation Capital     = 50 × $300,000    = $15,000,000',
    '',
    'Stranded Asset Exposure = $9,008,510 (32.9% of PPE — HIGH risk)',
])

# ── 17.6 COVENANTS ─────────────────────────────────────────────
doc.add_page_break()
add_heading(doc, '17.6  Debt Covenant Mechanics', 2, '#1e3a5f')

add_heading(doc, 'Status Thresholds', 3, '#2563eb')
add_table(doc,
    ['Status', 'Net Debt / EBITDA', 'Consequence'],
    [
        ['🟢 Green', '≤ 2.5×', 'No action. Banks comfortable.'],
        ['🟡 Amber', '2.5× to Trigger', 'Watch list. Banks requesting periodic updates.'],
        ['🔴 Red', 'Trigger to Trigger + 1.0×', '30-day cure period. Banks may restrict facility. +2% interest surcharge on net debt (6-month period).'],
        ['🚨 Breached', '> Trigger + 1.0×', 'Acceleration rights. Banks can demand full repayment. +5% surcharge. Solvency crisis.'],
    ],
    col_widths=[2.0, 3.5, 10.5]
)

doc.add_paragraph()
add_heading(doc, 'ESG-WACC Covenant Tightening', 3, '#2563eb')
add_para(doc, 'When ESG risk raises the cost of capital above 8%, lenders tighten the covenant trigger. This models the empirical finding that ESG risk tightens credit terms (El Ghoul et al., 2011):')
add_code_block(doc, [
    'If ESG-Adjusted WACC > 8%:',
    '  Tightening = (ESG-WACC − 8%) × 25',
    '  Effective Trigger = max(2.0×,  3.5× − Tightening)',
    '',
    'Example — ESG-WACC = 10%:',
    '  Tightening = (10% − 8%) × 25 = 0.5×',
    '  Effective Trigger = 3.5× − 0.5× = 3.0×',
    '  (Less room for leverage before covenant breach)',
    '',
    'Surcharge Formula:',
    '  Red covenant:     Net Debt × 2% ÷ 2 periods = per-round surcharge',
    '  Breached:         Net Debt × 5% ÷ 2 periods = per-round surcharge',
    '  Applied directly to corporate_treasury each round the breach persists.',
])

# ── 17.7 SENSITIVITIES ─────────────────────────────────────────
doc.add_page_break()
add_heading(doc, '17.7  Key Decision Sensitivities', 2, '#1e3a5f')
add_table(doc,
    ['Player Decision', 'Balance Sheet Effect', 'Mechanism'],
    [
        ['High CAPEX spend', '↑ PPE (60%), ↓ taxable income (40%)', 'Step 1: Capitalisation + expensing split'],
        ['Low CAPEX spend', '↓ PPE over time (depreciation erodes)', 'Step 2: Depreciation on opening balance'],
        ['NCD reduction (nature-based solutions)', '↓ Environmental provisions (may reverse to $1M floor)', 'Step 6: IAS 37 §59 reversal formula'],
        ['NCD increase', '↑ Environmental provisions ($5K per NCD unit)', 'Step 6: Linear NCD provision formula'],
        ['Reputation > 50', '↑ Brand value above base (1×)', 'Step 4: Rep factor > 1.0'],
        ['Reputation < 40', '↓ Goodwill impairment triggered (even rounds)', 'Step 4: Smooth impairment rate formula'],
        ['Reputation < 40 + low EBITDA margin', 'Dual-trigger: larger goodwill impairment', 'Step 4: Combined rep + margin rates'],
        ['Green bond issuance (R3 Scope 3)', '↑ NCL Green Bonds; ↑ interest expense', 'Step 6 (liability) + Step 7 (interest)'],
        ['High carbon intensity (CI > 60)', '↑ Stranded exposure; ↑ ESG-WACC → covenant tightening', 'Step 5 + Step 9'],
        ['Climate tipping point triggered', '↑ Stranded risk +15% (tipping modifier)', 'Step 5: Tipping tier modifier'],
        ['Dividends declared', 'Noted for scoring; RE is residual (not direct deduction)', 'Step 8: Closing identity absorbs all movements'],
        ['Low SLO scores', '↓ Brand value (sqrt dampening on SLO)', 'Step 4: SLO factor = √(SLO/50)'],
    ],
    col_widths=[4.5, 5.5, 6.0]
)

# ── 17.8 GOODWILL ─────────────────────────────────────────────
doc.add_page_break()
add_heading(doc, '17.8  Goodwill Impairment — Detailed Example (IAS 36)', 2, '#1e3a5f')
add_para(doc, 'Goodwill is tested for impairment every 2 rounds (Rounds 2, 4, 6, 8, 10 = annual equivalent). The test has a DUAL TRIGGER: reputation decline OR low EBITDA margin. The impairment rate is SMOOTH — no hard cliff at any threshold.')
add_code_block(doc, [
    'Impairment Rate Formulas:',
    '  Reputation trigger: if Reputation < 40:',
    '    Rep Rate   = max(0%, (40 − Reputation) ÷ 200)',
    '    At Rep=35: = (40−35) ÷ 200 = 2.5%',
    '    At Rep=20: = (40−20) ÷ 200 = 10.0%',
    '    At Rep=0:  = (40−0)  ÷ 200 = 20.0%  (maximum from reputation alone)',
    '',
    '  EBITDA margin trigger: if Margin < 10%:',
    '    Margin Rate = max(0%, (10% − Margin) × 0.5)',
    '    At Margin=8%:  = (10%−8%) × 0.5  = 1.0%',
    '    At Margin=0%:  = (10%−0%) × 0.5  = 5.0%  (maximum from margin alone)',
    '',
    '  Total Impairment Rate = min(30%, Rep Rate + Margin Rate)',
    '',
    'EXAMPLE — Round 4, Reputation=35, EBITDA Margin=12%:',
    '  Rep Rate    = (40−35) ÷ 200 = 2.5%',
    '  Margin Rate = max(0%, (10%−12%) × 0.5) = 0.0%  (margin above threshold)',
    '  Total Rate  = min(30%, 2.5% + 0.0%) = 2.5%',
    '  Goodwill impairment = $10,000,000 × 2.5% = $250,000',
    '  Goodwill closing    = $10,000,000 − $250,000 = $9,750,000',
    '',
    'COMPARE — Old hard-cliff model (pre-FIX-9):',
    '  Any reputation below 40 → fixed 10% impairment = $1,000,000',
    '  New smooth model at Rep=35 → $250,000  (4× less, proportionate)',
])

# ── 17.9 TEACHING NOTES ─────────────────────────────────────────
doc.add_page_break()
add_heading(doc, '17.9  Teaching Notes for Facilitators', 2, '#1e3a5f')

add_heading(doc, 'Why Retained Earnings Is a Residual, Not an Accumulator', 3, '#dc2626')
add_para(doc, 'Students will expect retained earnings to increase by exactly net income each round. In Muressons, retained earnings is derived as Net Assets − Share Capital − Other Reserves to maintain A = L + E at all times.')
add_para(doc, 'This is because the simulation uses a hybrid model: the treasury engine tracks cash flows as the primary mechanism, while the balance sheet is a parallel accrual layer. Simply adding raw net income to RE each tick creates an unmatched equity increase with no corresponding new asset. The closing identity approach resolves this correctly.')
add_para(doc, 'Key discussion point: "Reported earnings ≠ cash flows, and equity is always residual by construction — the balance sheet closes because we enforce it, not because every individual line is perfectly tracked."')
doc.add_paragraph()

add_heading(doc, 'Why Social Licence and Reputation Are NOT on the Balance Sheet', 3, '#dc2626')
add_para(doc, 'IAS 38 prohibits recognition of internally generated intangible assets. Social licence and reputation cannot be measured reliably and did not arise from a separable arm\'s-length transaction.')
add_para(doc, 'They are therefore disclosed only as supplementary non-GAAP <IR> Framework capitals — visible to players as an ESG disclosure, but explicitly excluded from Total Assets.')
add_para(doc, 'Discussion question: "Why would a pharmaceutical company\'s social licence score NOT appear on its audited balance sheet, even if that licence is worth hundreds of millions in market capitalisation terms?"')
doc.add_paragraph()

add_heading(doc, 'The Stranded Asset Conversation', 3, '#dc2626')
add_para(doc, 'The stranded asset calculation gives facilitators a concrete entry point for the Carbon Tracker / Net Zero transition discussion. In the Round 1 example, the corporation faces 32.9% stranded risk — meaning nearly a third of its physical asset base could face write-down in an accelerated transition scenario.')
add_para(doc, 'The Electronics BU (CI=72) is the primary driver. If players reduce Electronics\' carbon intensity below 40, CI Risk drops to ~20%, bringing Total Risk below 25% (moderate tier) and reducing exposure by ~$2.5M.')
doc.add_paragraph()

add_heading(doc, 'The ESG-WACC → Covenant Chain', 3, '#dc2626')
add_para(doc, 'The ESG-WACC → covenant tightening chain is the most powerful teaching mechanism in SE-6. Walk students through the full chain:')
for step in [
    '1. Poor ESG performance → higher carbon premium + governance penalty in ESG-WACC',
    '2. ESG-WACC > 8% → lenders tighten covenant trigger (0.25× per 1% excess)',
    '3. Tighter trigger → less room for leverage before covenant breach',
    '4. Covenant breach → treasury surcharge (2-5% on net debt per round) → cash pressure',
    '5. Cash pressure → fewer resources for CAPEX → slower decarbonisation → cycle repeats',
]:
    add_para(doc, step, indent=0.8)
add_para(doc, 'This chain makes ESG-financial integration mechanistically visible, not just theoretically stated. Every ESG decision has a traceable numerical pathway to the balance sheet and covenant position.')
doc.add_paragraph()

add_heading(doc, 'Common Student Misunderstandings', 3, '#2563eb')
add_table(doc,
    ['Misunderstanding', 'Correct Understanding'],
    [
        ['Dividends reduce net income', 'Dividends are an equity distribution. They appear below net income and reduce the residual equity position, not the P&L.'],
        ['Social licence is an asset on the balance sheet', 'IAS 38 prohibits internally generated intangibles. SLO capital is a non-GAAP <IR> Framework disclosure only.'],
        ['Higher CAPEX always improves the balance sheet', '40% of CAPEX is expensed immediately, reducing taxable income. Only 60% creates a PPE asset. Net effect depends on the balance.'],
        ['Goodwill falls sharply at reputation = 40', 'The smooth formula means 5 reputation points below 40 produces a 2.5% impairment rate. The cliff has been removed.'],
        ['Net Debt / EBITDA uses gross profit', 'True EBITDA = Gross Profit + Depreciation (D&A is added back). Using gross profit understates EBITDA and overstates the ratio.'],
        ['Covenant breach is permanent', 'Breach status is recalculated each round. Reducing net debt (paying down RCF) or improving EBITDA will restore green status.'],
    ],
    col_widths=[6.0, 10.0]
)

# ── SAVE ──────────────────────────────────────────────────────
output_path = '../docs/Section_17_Balance_Sheet_Engine.docx'
doc.save(output_path)
print(f'Saved: {output_path}')
print(f'Pages: approx 18-22')
