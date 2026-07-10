"""
append_balance_sheet_glossary.py
---------------------------------
Appends "Appendix: Balance Sheet — Statement of Financial Position
Glossary & Facilitator Reference" to:
  - Muressons_Facilitator_Manual_v8.docx  (Facilitator Manual)

Outputs versioned copy:
  - Muressons_Facilitator_Manual_v9.docx
"""

import os
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

BASE_DIR = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim"

FACILITATOR_MANUAL = os.path.join(
    BASE_DIR, "Muressons_Facilitator_Manual_v8.docx"
)

# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────
def add_heading(doc, text, level=1):
    doc.add_heading(text, level=level)


def add_body(doc, text):
    p = doc.add_paragraph(text)
    p.style.font.size = Pt(11)
    return p


def add_bold_body(doc, text):
    """Body paragraph with bold emphasis."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    return p


def add_bullet(doc, text):
    doc.add_paragraph(text, style='List Bullet')


def add_italic_note(doc, text):
    """Italic note paragraph for IFRS references and simulation notes."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    return p


def add_formula(doc, text):
    """Monospaced formula block."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    p.paragraph_format.left_indent = Cm(1)
    return p


def add_table(doc, headers, rows):
    """Add a formatted table with header row."""
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = 'Light Grid Accent 1'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        t.rows[0].cells[i].text = h
        for run in t.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
    for ri, row in enumerate(rows, 1):
        for ci, val in enumerate(row):
            t.rows[ri].cells[ci].text = str(val)
    doc.add_paragraph()  # spacer


# ─────────────────────────────────────────────────────────────────
#  APPENDIX CONTENT
# ─────────────────────────────────────────────────────────────────
def add_balance_sheet_appendix(doc):
    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════
    #  TITLE
    # ═══════════════════════════════════════════════════════════════
    add_heading(doc, 'Appendix: Balance Sheet — Statement of Financial Position', level=1)

    add_body(doc,
        'This appendix provides facilitators with a complete reference to every line item, '
        'subtotal, ratio, and indicator displayed on the Muressons balance sheet (Statement '
        'of Financial Position). For each item, we explain what it represents in real-world '
        'corporate finance, the IFRS standard that governs it, how it is calculated in the '
        'simulation engine, and common misunderstandings that students may exhibit.'
    )

    add_body(doc,
        'A balance sheet (formally: Statement of Financial Position under IFRS/IAS 1) is a '
        'snapshot of what a company owns (Assets), what it owes (Liabilities), and what is '
        'left over for shareholders (Equity) at a single point in time. The fundamental '
        'accounting identity is:'
    )

    add_formula(doc, 'Assets = Liabilities + Equity')

    add_body(doc,
        'This identity must always hold. In the Muressons simulation, the balance sheet '
        'engine enforces this by deriving Retained Earnings as the residual figure after '
        'all asset and liability lines are independently updated each round.'
    )

    # ═══════════════════════════════════════════════════════════════
    #  SECTION 1 — SAMPLE BALANCE SHEET
    # ═══════════════════════════════════════════════════════════════
    add_heading(doc, 'A1.1 Sample Balance Sheet Layout', level=2)

    add_body(doc,
        'The following table shows a representative balance sheet as displayed in the '
        'simulation\'s Executive Cockpit. This particular example reflects a company '
        'in severe financial distress — a common outcome when students neglect financial '
        'sustainability in pursuit of ESG improvements.'
    )

    add_table(doc,
        ['Assets', 'Value', 'Liabilities & Equity', 'Value'],
        [
            ['Non-Current Assets', '', 'Non-Current Liabilities', ''],
            ['  Property, Plant & Equipment', '$6.3M', '  Revolving Credit Facility', '$50.0M'],
            ['  Right-of-Use Assets (IFRS 16)', '$7.5M', '  Green Bonds Outstanding', '$0K'],
            ['  Inventory', '$77.1M', '  Environmental Provisions', '$1.0M'],
            ['', '', '  Decommissioning Obligations', '$3.0M'],
            ['', '', '  Lease Liabilities (IFRS 16)', '$6.6M'],
            ['Total Tangible Assets', '$90.9M', 'Total Non-Current Liabilities', '$60.6M'],
            ['', '', '', ''],
            ['Intangible Assets', '', 'Current Liabilities', ''],
            ['  Brand Value', '$5.8M', '  Trade Payables', '$55.1M'],
            ['  Intellectual Property', '$23.0M', '  Tax Provisions', '$0K'],
            ['  Goodwill', '$10.0M', '  Accrued Remediation', '$0K'],
            ['', '', '  Short-Term Debt', '$0K'],
            ['Total Intangible Assets', '$38.8M', 'Total Current Liabilities', '$55.1M'],
            ['', '', '', ''],
            ['Current Assets', '', 'TOTAL LIABILITIES', '$115.8M'],
            ['  Cash & Equivalents', '-$521.1M', '', ''],
            ['  Trade Receivables', '$3.0M', "Shareholders' Equity", ''],
            ['  Prepayments', '$1.0M', '  Share Capital', '$30.0M'],
            ['', '', '  Retained Earnings', '-$524.2M'],
            ['Total Current Assets', '-$517.1M', '  Other Reserves', '$5.0M'],
            ['', '', 'TOTAL EQUITY', '-$489.2M'],
            ['TOTAL ASSETS', '-$373.4M', 'NET ASSETS (= Equity)', '-$489.2M'],
        ]
    )

    # ═══════════════════════════════════════════════════════════════
    #  SECTION 2 — NON-CURRENT ASSETS
    # ═══════════════════════════════════════════════════════════════
    add_heading(doc, 'A1.2 Non-Current Assets (Tangible)', level=2)

    add_body(doc,
        'Non-current assets are resources the company expects to hold for more than '
        '12 months. These are the long-term physical and financial resources that '
        'power the business.'
    )

    # ── PP&E ──
    add_heading(doc, 'Property, Plant & Equipment (PP&E)', level=3)
    add_body(doc,
        'The physical assets used in operations — factories, machinery, vehicles, '
        'mining equipment, and office buildings. Anything the company uses to produce '
        'goods or deliver services.'
    )
    add_body(doc,
        'Real-World Example: A mining company\'s excavators, processing plants, and '
        'conveyor belts. A hotel chain\'s property portfolio.'
    )
    add_bold_body(doc, 'How it works in the simulation:')
    add_bullet(doc,
        'When players allocate CAPEX, a portion (the capitalisation rate) is added to '
        'PP&E rather than expensed immediately.'
    )
    add_bullet(doc,
        'Each round, PP&E depreciates at 5% per 6-month round (10% annual, representing '
        'a ~10-year useful life for industrial equipment via straight-line depreciation).'
    )
    add_bullet(doc,
        'New CAPEX is depreciated starting from the NEXT period only (per IAS 16 §55: '
        'depreciation begins when the asset is available for use).'
    )
    add_italic_note(doc, 'IFRS Standard: IAS 16 — Property, Plant and Equipment')

    # ── ROU ──
    add_heading(doc, 'Right-of-Use Assets (IFRS 16)', level=3)
    add_body(doc,
        'The value of assets the company leases rather than owns — typically office space, '
        'warehouses, or equipment on long-term contracts. Before IFRS 16 (effective 2019), '
        'operating leases were hidden off the balance sheet. The standard now requires '
        'them to be recognised as both an asset (here) and a liability (Lease Liabilities).'
    )
    add_body(doc,
        'Real-World Example: A 20-year lease on a headquarters building. The company '
        'doesn\'t own the building, but the right to use it has economic value.'
    )
    add_bold_body(doc, 'How it works in the simulation:')
    add_bullet(doc,
        'At initialisation, ROU assets are set to 40% of total revenue (proxy for '
        'lease commitments relative to company size).'
    )
    add_bullet(doc,
        'Depreciates at 2.5% per round (5% annual, ~20-year property lease term).'
    )
    add_italic_note(doc, 'IFRS Standard: IFRS 16 — Leases')

    # ── Inventory ──
    add_heading(doc, 'Inventory', level=3)
    add_body(doc,
        'Physical goods the company holds — raw materials waiting to be processed, '
        'work-in-progress on the production line, and finished goods ready to sell.'
    )
    add_body(doc,
        'Real-World Example: Stockpiles of iron ore at a mine site, chemicals in a '
        'warehouse, or packaged goods ready for shipment.'
    )
    add_bold_body(doc, 'How it works in the simulation:')
    add_bullet(doc,
        'Calculated as a 60-day stock level based on operating expenses: '
        'Inventory = (Annual OPEX ÷ 365) × 60 days.'
    )
    add_bullet(doc,
        'Updated dynamically each round as OPEX changes.'
    )
    add_italic_note(doc,
        'IFRS Standard: IAS 2 — Inventories. Note: Under IAS 1, inventory would '
        'normally be classified as a current asset. The simulation places it under '
        'tangible assets for presentational simplicity — a simplification that '
        'facilitators may wish to discuss with advanced students.'
    )

    # ═══════════════════════════════════════════════════════════════
    #  SECTION 3 — INTANGIBLE ASSETS
    # ═══════════════════════════════════════════════════════════════
    add_heading(doc, 'A1.3 Intangible Assets', level=2)

    add_body(doc,
        'Assets that have value but no physical form. They cannot be seen or touched, '
        'but they generate economic benefits for the company.'
    )

    # ── Brand Value ──
    add_heading(doc, 'Brand Value', level=3)
    add_body(doc,
        'The monetary value of the company\'s brand name — the premium customers '
        'are willing to pay because of the company\'s reputation and recognition.'
    )
    add_body(doc,
        'Real-World Example: The Coca-Cola brand is estimated to be worth over $80 '
        'billion. People pay more for Coke than for a generic cola because of the brand.'
    )
    add_bold_body(doc, 'Simulation formula:')
    add_formula(doc,
        'Brand = Base × (Reputation ÷ 50) × √(Social Licence ÷ 50)\n'
        'Floor: $1M minimum (residual brand value always exists)\n'
        'Base is FIXED at initialisation — prevents exponential compounding (FIX-2).'
    )
    add_italic_note(doc,
        'IFRS Standard: IAS 38 — Intangible Assets. Only acquired brands can be '
        'recognised under IFRS. Internally generated brands cannot be capitalised.'
    )

    # ── IP ──
    add_heading(doc, 'Intellectual Property (IP)', level=3)
    add_body(doc,
        'Patents, proprietary technologies, trade secrets, copyrights, and other '
        'knowledge-based assets that give the company a competitive advantage.'
    )
    add_body(doc,
        'Real-World Example: A pharmaceutical company\'s drug patents, a tech '
        'company\'s software algorithms, or a manufacturer\'s proprietary process.'
    )
    add_bold_body(doc, 'How it works in the simulation:')
    add_bullet(doc,
        'Set at initialisation: $15M base + $2M per BU. Fixed throughout unless '
        'impairment is triggered.'
    )
    add_italic_note(doc, 'IFRS Standard: IAS 38 — Intangible Assets')

    # ── Goodwill ──
    add_heading(doc, 'Goodwill', level=3)
    add_body(doc,
        'The premium paid when acquiring another company above the fair value of its '
        'identifiable net assets. Represents customer relationships, employee expertise, '
        'synergies, and market position that cannot be individually valued.'
    )
    add_body(doc,
        'Real-World Example: If Company A buys Company B for $50M, but Company B\'s '
        'identifiable assets minus liabilities are only worth $40M, the extra $10M '
        'is recorded as goodwill.'
    )
    add_bold_body(doc, 'Key accounting rules:')
    add_bullet(doc,
        'Goodwill is NEVER amortised (written down gradually) — instead, it must be '
        'tested for impairment at least annually (IAS 36).'
    )
    add_bullet(doc,
        'In the simulation, impairment is tested every 2 rounds (annual equivalent) '
        'with a dual trigger: reputation < 40 OR EBITDA margin < 10%.'
    )
    add_bullet(doc,
        'Impairment uses a smooth continuous formula rather than a cliff: '
        'Rep_Rate = max(0, (40 − Rep) / 200); Margin_Rate = max(0, (0.10 − Margin) × 0.5). '
        'Combined rate capped at 30% per test.'
    )
    add_italic_note(doc,
        'IFRS Standards: IFRS 3 — Business Combinations (recognition); '
        'IAS 36 — Impairment of Assets (annual testing)'
    )

    # ── Non-GAAP ESG Capitals ──
    add_heading(doc, 'Non-GAAP ESG Capitals (Off-Balance-Sheet Disclosures)', level=3)
    add_body(doc,
        'Two additional capital items are displayed on the balance sheet with a "†" marker '
        'but are explicitly excluded from Total Assets:'
    )
    add_bullet(doc,
        'Social Licence Capital — a monetary estimate of community trust and acceptance '
        '(calculated as Average SLO Score × $200K).'
    )
    add_bullet(doc,
        'Reputation Capital — a monetary estimate of corporate reputation '
        '(calculated as Group Reputation Score × $300K).'
    )
    add_body(doc,
        'These items are disclosed under the Integrated Reporting <IR> Framework\'s '
        'Six Capitals model for pedagogical purposes. Under IAS 38, internally generated '
        'intangibles (brands, mastheads, customer relationships) cannot be recognised as '
        'assets because their cost cannot be reliably measured.'
    )
    add_bold_body(doc, 'Scholarly ESG Toggle (Facilitator Feature):')
    add_body(doc,
        'Facilitators can activate the "Scholarly View" toggle in God Mode to move these '
        'items onto the GAAP balance sheet as intangible assets. This is a pedagogical '
        '"what-if" mode that explores the academic debate around recognising social and '
        'natural capital. When activated, a prominent amber banner appears and Total Assets '
        'increases by the ESG capital amounts. References: IIRC <IR> Framework (2021); '
        'Barker & Eccles (2011); Gleeson-White (2014).'
    )

    # ═══════════════════════════════════════════════════════════════
    #  SECTION 4 — CURRENT ASSETS
    # ═══════════════════════════════════════════════════════════════
    add_heading(doc, 'A1.4 Current Assets', level=2)

    add_body(doc,
        'Assets the company expects to convert to cash within 12 months — the liquid, '
        'short-term resources.'
    )

    # ── Cash ──
    add_heading(doc, 'Cash & Equivalents', level=3)
    add_body(doc,
        'Money in the bank — cash on hand, bank deposits, and highly liquid short-term '
        'investments (like money market funds) that can be converted to cash almost instantly.'
    )
    add_bold_body(doc, 'How it works in the simulation:')
    add_bullet(doc,
        'Synced from the corporate_treasury variable each round (single source of truth).'
    )
    add_bullet(doc,
        'Can go negative — representing a massive bank overdraft. In real IFRS practice, '
        'overdrafts repayable on demand would typically be reclassified as a current '
        'liability (IAS 7/IAS 1), but the simulation retains them here for simplicity.'
    )
    add_italic_note(doc,
        'Facilitator Discussion Point: Ask students whether a -$521M cash balance '
        'should be shown as a negative asset or reclassified as a liability. '
        'What changes in the balance sheet presentation? (Answer: Total Assets '
        'increases, Total Liabilities increases by the same amount, Equity is unchanged.)'
    )

    # ── Trade Receivables ──
    add_heading(doc, 'Trade Receivables', level=3)
    add_body(doc,
        'Money that customers owe the company for goods or services already delivered '
        'but not yet paid for. Essentially, invoices sent but payment not yet received.'
    )
    add_bold_body(doc, 'Simulation formula:')
    add_formula(doc,
        'DSO_Factor = min(0.25, 0.12 + 0.001 × Avg_Governance_Risk)\n'
        'Trade_Receivables = Total_Revenue × DSO_Factor'
    )
    add_bullet(doc,
        'Higher governance risk → longer Days Sales Outstanding (DSO) → higher receivables.'
    )
    add_italic_note(doc, 'IFRS Standard: IFRS 9 — Financial Instruments; IFRS 15 — Revenue from Contracts')

    # ── Prepayments ──
    add_heading(doc, 'Prepayments', level=3)
    add_body(doc,
        'Money the company has paid in advance for goods or services it hasn\'t received '
        'yet — insurance premiums paid upfront, rent paid ahead of time, or deposits on '
        'future orders.'
    )
    add_bullet(doc, 'Set at $250K per BU at initialisation. Fixed throughout the simulation.')

    # ═══════════════════════════════════════════════════════════════
    #  SECTION 5 — NON-CURRENT LIABILITIES
    # ═══════════════════════════════════════════════════════════════
    add_heading(doc, 'A1.5 Non-Current Liabilities', level=2)

    add_body(doc,
        'Debts and obligations the company must pay, but not within the next 12 months. '
        'These are long-term commitments.'
    )

    # ── Revolving Credit ──
    add_heading(doc, 'Revolving Credit Facility', level=3)
    add_body(doc,
        'A pre-arranged line of credit with a bank — like a corporate credit card. '
        'The company can draw down funds, repay them, and draw again up to the agreed limit.'
    )
    add_bullet(doc,
        'Set at $12.5M per BU ($50M for standard 4-BU configuration).'
    )
    add_bullet(doc,
        'This is the primary loan facility. If covenants are breached, the bank can '
        '"accelerate" — demand immediate full repayment.'
    )

    # ── Green Bonds ──
    add_heading(doc, 'Green Bonds Outstanding', level=3)
    add_body(doc,
        'Bonds issued specifically to fund environmentally beneficial projects — '
        'renewable energy, pollution reduction, sustainable infrastructure. Issued by '
        'player decision (e.g. Round 3 Scope 3 investment option).'
    )
    add_body(doc,
        'Real-World Example: Apple issued $4.7B in green bonds to fund clean energy '
        'and recycling initiatives.'
    )

    # ── Environmental Provisions ──
    add_heading(doc, 'Environmental Provisions', level=3)
    add_body(doc,
        'Money set aside for expected future environmental cleanup costs — soil '
        'remediation, water treatment, pollution cleanup, or habitat restoration '
        'that the company is legally obligated to perform.'
    )
    add_bold_body(doc, 'Simulation formula:')
    add_formula(doc,
        'NCD_Provision = NCD × $20,000 per unit\n'
        'Event_Provision = Number_of_Remediation_Events × $500,000\n'
        'Total = max(Minimum_Floor, NCD_Provision + Event_Provision)'
    )
    add_bullet(doc,
        'Provisions can DECREASE when Natural Capital Debt falls — IAS 37 §59 permits '
        'reversal of provisions when the obligating event no longer exists. This was '
        'a deliberate design choice (FIX-6) to reward students who invest in '
        'nature-based solutions.'
    )
    add_italic_note(doc, 'IFRS Standard: IAS 37 — Provisions, Contingent Liabilities and Contingent Assets')

    # ── Decommissioning ──
    add_heading(doc, 'Decommissioning Obligations', level=3)
    add_body(doc,
        'The estimated cost of dismantling and removing assets at the end of their '
        'useful life — tearing down a factory, plugging an oil well, or restoring '
        'a mine site to its natural state.'
    )
    add_bullet(doc,
        'Recorded at present value at initialisation ($750K per BU).'
    )
    add_bullet(doc,
        'Grows each round through "accretion" — adding back the time-value-of-money '
        'component (3% annual discount rate, halved for 6-month periods).'
    )
    add_italic_note(doc, 'IFRS Standard: IAS 37 + IFRIC 1 — Changes in Existing Decommissioning Liabilities')

    # ── Lease Liabilities ──
    add_heading(doc, 'Lease Liabilities (IFRS 16)', level=3)
    add_body(doc,
        'The counterpart to the Right-of-Use Asset. This is the total remaining '
        'obligation to make lease payments over the life of the lease.'
    )
    add_bullet(doc,
        'Initialised at 35% of total revenue (slightly less than ROU at 40%, '
        'representing the advance-payment component).'
    )
    add_bullet(doc,
        'Amortises at 2.5% per round (5% annual, matching the 20-year lease term).'
    )
    add_italic_note(doc, 'IFRS Standard: IFRS 16 — Leases')

    # ═══════════════════════════════════════════════════════════════
    #  SECTION 6 — CURRENT LIABILITIES
    # ═══════════════════════════════════════════════════════════════
    add_heading(doc, 'A1.6 Current Liabilities', level=2)

    add_body(doc, 'Debts and obligations due within the next 12 months.')

    add_heading(doc, 'Trade Payables', level=3)
    add_body(doc,
        'Money the company owes to its suppliers for goods and services already received '
        'but not yet paid for. The mirror image of Trade Receivables.'
    )
    add_bold_body(doc, 'Simulation formula:')
    add_formula(doc,
        'DPO_Factor = min(0.18, 0.10 + 0.0005 × Avg_Governance_Risk)\n'
        'Trade_Payables = Total_OPEX × DPO_Factor'
    )
    add_italic_note(doc,
        'Facilitator Discussion Point: When payables greatly exceed receivables '
        '(e.g. $55M vs $3M), it signals the company is stretching supplier payments '
        'to conserve cash — a classic indicator of financial distress.'
    )

    add_heading(doc, 'Tax Provisions', level=3)
    add_body(doc,
        'Tax the company expects to owe based on current-period profits. Zero when '
        'the company is making losses (no taxable income = no tax provision).'
    )
    add_formula(doc,
        'Tax_Provisions = max(0, Gross_Profit × Tax_Rate × 0.20)'
    )

    add_heading(doc, 'Accrued Remediation', level=3)
    add_body(doc,
        'Short-term environmental cleanup costs due within 12 months, triggered by '
        'specific crisis events during the simulation.'
    )

    add_heading(doc, 'Short-Term Debt', level=3)
    add_body(doc,
        'Loans or borrowings due within one year — bank loans, commercial paper, '
        'or the current portion of long-term debt.'
    )

    # ═══════════════════════════════════════════════════════════════
    #  SECTION 7 — EQUITY
    # ═══════════════════════════════════════════════════════════════
    add_heading(doc, "A1.7 Shareholders' Equity", level=2)

    add_body(doc,
        'What remains for shareholders after subtracting all liabilities from all assets. '
        'This is the owners\' residual claim on the company.'
    )

    add_heading(doc, 'Share Capital', level=3)
    add_body(doc,
        'The money originally invested by shareholders when the company issued its shares. '
        'This is "permanent" capital that does not change unless new shares are issued or '
        'existing shares are bought back.'
    )
    add_bullet(doc, 'Set at $7.5M per BU ($30M for 4 BUs). Fixed throughout the simulation.')

    add_heading(doc, 'Retained Earnings', level=3)
    add_body(doc,
        'The cumulative total of all profits ever earned minus all dividends ever paid '
        'since the company was founded. This is the running scorecard of whether the '
        'business has been profitable over its entire history.'
    )
    add_bold_body(doc, 'How it works in the simulation:')
    add_body(doc,
        'Rather than tracking profit/loss incrementally, the simulation derives Retained '
        'Earnings as a RESIDUAL to force the balance sheet to balance:'
    )
    add_formula(doc,
        'Retained_Earnings = Total_Assets − Total_Liabilities − Share_Capital − Other_Reserves'
    )
    add_body(doc,
        'This means Retained Earnings absorbs all movements in assets and liabilities. '
        'When cash drops, Retained Earnings drops by the same amount. When liabilities '
        'increase, Retained Earnings decreases. The net_income figure from the income '
        'statement is preserved in diagnostics for scoring and teaching purposes.'
    )

    add_heading(doc, 'Other Reserves', level=3)
    add_body(doc,
        'A catch-all for equity items that aren\'t Share Capital or Retained Earnings — '
        'revaluation reserves, foreign currency translation reserves, and hedging reserves.'
    )
    add_bullet(doc, 'Set at $1.25M per BU ($5M for 4 BUs). Fixed throughout the simulation.')

    # ═══════════════════════════════════════════════════════════════
    #  SECTION 8 — KEY RATIOS
    # ═══════════════════════════════════════════════════════════════
    add_heading(doc, 'A1.8 Key Ratios & Covenant Status', level=2)

    add_heading(doc, 'Debt / Equity Ratio', level=3)
    add_body(doc,
        'Measures how much debt the company uses relative to shareholders\' equity — '
        'a measure of financial leverage.'
    )
    add_formula(doc,
        'D/E = Total_Liabilities ÷ Total_Equity\n'
        'Normal range: 0.5x to 2.0x\n'
        'Capped at 99x when equity is negative (ratio is meaningless)'
    )

    add_heading(doc, 'Net Debt / EBITDA', level=3)
    add_body(doc,
        'Measures how many years of earnings it would take to repay all net debt. '
        'The primary covenant metric used by banks.'
    )
    add_formula(doc,
        'Net_Debt = (Revolving_Credit + Green_Bonds + Short_Term_Debt) − Cash\n'
        'EBITDA = Gross_Profit + Depreciation  (FIX-4: true EBITDA with D&A addback)\n'
        'Ratio = Net_Debt ÷ EBITDA\n'
        'Capped at 99x when EBITDA is zero or negative'
    )

    add_heading(doc, 'Stranded Asset Exposure', level=3)
    add_body(doc,
        'The dollar value of physical assets at risk of becoming worthless due to the '
        'transition to a low-carbon economy. Based on Carbon Tracker Initiative methodology.'
    )
    add_formula(doc,
        'CI_Risk = min(0.5, Carbon_Intensity_Avg ÷ 200)\n'
        'Total_Risk = min(0.80, CI_Risk + Pathway_Risk + Tipping_Risk)\n'
        'Stranded_Exposure = PP&E × Total_Risk'
    )

    add_heading(doc, 'Covenant Status', level=3)
    add_body(doc,
        'Covenants are conditions in the company\'s loan agreements. Breach triggers '
        'escalating consequences:'
    )
    add_table(doc,
        ['Status', 'Condition', 'Consequence'],
        [
            ['🟢 Comfortable', 'ND/EBITDA ≤ 2.5x', 'Banks satisfied. No action required.'],
            ['🟡 Watch List', '2.5x < ND/EBITDA ≤ Trigger', 'Banks request periodic updates.'],
            ['🔴 Breach', 'Trigger < ND/EBITDA ≤ Trigger + 1.0x', '30-day cure period. 2% interest surcharge.'],
            ['🚨 Acceleration', 'ND/EBITDA > Trigger + 1.0x', 'Banks can demand immediate repayment. 5% surcharge.'],
        ]
    )
    add_body(doc,
        'The trigger ratio is dynamic — it tightens when the ESG-Adjusted WACC exceeds '
        '8% (by -0.25x per 1% excess). This models the empirical finding that ESG risk '
        'increases lender scrutiny (El Ghoul et al., 2011).'
    )

    # ═══════════════════════════════════════════════════════════════
    #  SECTION 9 — COMMON STUDENT MISCONCEPTIONS
    # ═══════════════════════════════════════════════════════════════
    add_heading(doc, 'A1.9 Common Student Misconceptions & Facilitator Responses', level=2)

    add_table(doc,
        ['Misconception', 'Correct Understanding', 'Suggested Response'],
        [
            ['"Negative cash means we\'re bankrupt."',
             'Negative cash means a bank overdraft. Insolvency depends on whether total liabilities exceed total assets (i.e. negative equity).',
             '"Is the company insolvent because of the cash, or because of the accumulated losses? What does equity tell you?"'],

            ['"We should maximise Total Assets."',
             'Asset growth is only valuable if it generates returns above cost of capital. Accumulating unproductive assets destroys value.',
             '"What is the Return on Assets? Is growing the asset base actually creating shareholder value?"'],

            ['"Goodwill never changes."',
             'Goodwill must be tested for impairment annually. Low reputation or poor margins trigger write-downs.',
             '"What happens to goodwill when the company\'s reputation drops below 40? Check the IAS 36 impairment trigger."'],

            ['"The † ESG items should be included in our assets."',
             'IAS 38 prohibits capitalising internally generated intangibles. The <IR> Framework advocacy for this is a scholarly debate, not current GAAP.',
             '"Activate the Scholarly Toggle and compare the two views. What would change if regulators accepted the <IR> Framework argument?"'],

            ['"High trade payables is good — we\'re conserving cash."',
             'Stretching supplier payments signals distress and damages supplier relationships. It is a symptom, not a strategy.',
             '"What happens to your supply chain when suppliers learn you can\'t pay? Compare payables to receivables — what does the 18:1 ratio tell you?"'],
        ]
    )

    # ═══════════════════════════════════════════════════════════════
    #  SECTION 10 — ACCOUNTING EQUATION WALKTHROUGH
    # ═══════════════════════════════════════════════════════════════
    add_heading(doc, 'A1.10 Accounting Equation — Worked Walkthrough', level=2)

    add_body(doc,
        'This section walks through the fundamental accounting identity using the '
        'sample balance sheet above, demonstrating how every subtotal connects:'
    )

    add_formula(doc,
        'ASSETS:\n'
        '  Total Tangible Assets:     $6.3M + $7.5M + $77.1M      =  $90.9M\n'
        '  Total Intangible Assets:   $5.8M + $23.0M + $10.0M     =  $38.8M\n'
        '  Total Current Assets:      -$521.1M + $3.0M + $1.0M    = -$517.1M\n'
        '  TOTAL ASSETS:              $90.9M + $38.8M + (-$517.1M) = -$387.4M\n'
        '\n'
        'LIABILITIES:\n'
        '  Total Non-Current:         $50.0M + $0 + $1.0M + $3.0M + $6.6M = $60.6M\n'
        '  Total Current:             $55.1M + $0 + $0 + $0               = $55.1M\n'
        '  TOTAL LIABILITIES:         $60.6M + $55.1M                     = $115.7M\n'
        '\n'
        'EQUITY:\n'
        '  Share Capital + Retained Earnings + Other Reserves\n'
        '  = $30.0M + (-$524.2M) + $5.0M = -$489.2M\n'
        '\n'
        'VERIFICATION:\n'
        '  Net Assets = Total Assets − Total Liabilities\n'
        '             = -$387.4M − $115.7M = -$503.1M\n'
        '  Total Equity = -$489.2M\n'
        '  ✓ A = L + E holds (minor rounding differences from display formatting)'
    )

    add_body(doc,
        'The key insight for students: Retained Earnings of -$524.2M means the company '
        'has destroyed $524M of value over its lifetime. Starting from $35M of original '
        'equity (Share Capital + Reserves), the business has burned through all of it '
        'and then some — resulting in a net equity hole of -$489M. This is technical '
        'insolvency: liabilities exceed assets, and shareholders\' claims are worthless.'
    )


# ─────────────────────────────────────────────────────────────────
#  RUNNER
# ─────────────────────────────────────────────────────────────────
def process(filepath, add_fn, label, output_name):
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return

    doc = docx.Document(filepath)
    add_fn(doc)

    out = os.path.join(BASE_DIR, output_name)
    doc.save(out)
    print(f"[OK] {label} saved -> {output_name}")


if __name__ == '__main__':
    process(
        FACILITATOR_MANUAL,
        add_balance_sheet_appendix,
        "Facilitator Manual",
        "Muressons_Facilitator_Manual_v9.docx",
    )
