"""Appendix D: Architecture Blueprint — Module Design Standard.

Renders the full Architecture Blueprint (blueprint.md) as a formatted
DOCX appendix in the Muressons Facilitator Manual.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from docx_styles import (
    add_page_break, add_styled_table, add_callout, add_bullet_list,
    BRAND_NAVY, BRAND_BLUE, BRAND_TEAL, BRAND_GREEN, BRAND_AMBER,
    BRAND_GRAY, WHITE, LIGHT_GRAY,
)
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml


# ── Colour helpers ────────────────────────────────────────────────────────────

def _shade_cell(cell, hex_colour: str):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_colour}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def _add_section_rule(doc):
    """Thin horizontal rule paragraph for visual separation."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run("─" * 90)
    run.font.size = Pt(7)
    run.font.color.rgb = BRAND_GRAY


def _add_mono_para(doc, text: str):
    """Monospaced paragraph for template / code blocks."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.4)
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(text)
    run.font.name = "Courier New"
    run.font.size = Pt(9)
    run.font.color.rgb = BRAND_TEAL


def _add_label_value(doc, label: str, value: str, indent: float = 0.3):
    """Bold label followed by body text on the same paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(indent)
    p.paragraph_format.space_after = Pt(4)
    r1 = p.add_run(label + "  ")
    r1.font.bold = True
    r1.font.size = Pt(10)
    r1.font.color.rgb = BRAND_NAVY
    r2 = p.add_run(value)
    r2.font.size = Pt(10)


# ── Module detail cards ───────────────────────────────────────────────────────

_MODULES = [
    {
        "id": "D.2.1",
        "name": "Carbon Accounting Helpers",
        "file": "backend/engine.py",
        "functions": "get_scope_ratios · calc_revenue_weighted_avg_ci · apply_ci_delta_to_bus",
        "goal": (
            "Centralise all GHG Protocol Scope 1/2/3 calculations to ensure consistent "
            "carbon-intensity accounting across all Business Units and industry verticals, "
            "replacing prior per-function scope estimates."
        ),
        "invariants": [
            "scope_1 + scope_2 + scope_3 == 1.0 for every BU in _ALL_BU_SCOPE_RATIOS.",
            "Revenue-weighted avg CI falls back to simple arithmetic mean when total revenue is zero.",
            "carbon_intensity is always >= 0.0 after any delta is applied.",
        ],
        "deps": [
            "ECONOMIC_CARBON_PRICE_BASE, ECONOMIC_CARBON_PRICE_GROWTH — from config.py.",
            "bu_id, carbon_intensity, revenue_base — from bu_states list.",
        ],
        "edge_cases": [
            "Empty bus list → return _DEFAULT_SCOPE_RATIOS.",
            "Unknown bu_id → fallback to _DEFAULT_SCOPE_RATIOS.",
            "All revenues zero → simple arithmetic mean.",
            "Negative ci_delta with scope3_weighted routing on low-Scope3 BU — verify factor = 0.70.",
        ],
    },
    {
        "id": "D.2.2",
        "name": "Corporate Strategic Fund (CSF)",
        "file": "backend/engine.py",
        "functions": "calc_csf",
        "goal": (
            "Compute net cash added to the corporate treasury each round: "
            "CSF = Σ(Revenue_Base − OPEX_Base) − Dividends_Paid."
        ),
        "invariants": [
            "CSF may be negative (deficit round).",
            "Result must equal gross_profit minus dividends exactly — no rounding on the subtraction.",
        ],
        "deps": [
            "revenue_base, opex_base — from every BU state dict.",
            "dividends_paid — from player decision payload.",
        ],
        "edge_cases": [
            "Empty BU list → gross_profit = 0.",
            "dividends_paid larger than gross profit → negative CSF is valid.",
            "Floating-point precision: sum then subtract to preserve precision.",
        ],
    },
    {
        "id": "D.2.3",
        "name": "Contagion Engine (Sigmoid Model)",
        "file": "backend/engine.py",
        "functions": "calc_contagion",
        "goal": (
            "Model crisis propagation via an S-curve so low-severity events cause minimal "
            "reputation impact, mid-range events cause rapid erosion, and high-severity events "
            "plateau. Group_Rep = Avg_Rep − 50 × sigmoid((severity − 30) / 15)."
        ),
        "invariants": [
            "Output clamped to [0, 100].",
            "crisis_severity is floored at 0 before sigmoid (no negative severity).",
            "Empty bu_states returns 50.0.",
        ],
        "deps": [
            "reputation_score — per BU.",
            "crisis_severity — from black_swan_registry.py or round event payload.",
        ],
        "edge_cases": [
            "crisis_severity = 0 → minimal damage.",
            "crisis_severity = 100 → near-maximum damage.",
            "Empty bu_states → 50.0.",
            "crisis_severity < 0 → clamp to 0.",
        ],
    },
    {
        "id": "D.2.4",
        "name": "Synergy Engine (Diminishing Returns)",
        "file": "backend/engine.py",
        "functions": "calc_synergy_opex",
        "goal": (
            "Model efficiency gains from cross-BU investment with a square-root curve so "
            "early dollars yield outsized returns and later dollars face diminishing marginal "
            "efficiency. New_OPEX = Old_OPEX × (1 − √ratio × 0.7 × Synergy_Multiplier)."
        ),
        "invariants": [
            "investment_ratio clamped to [0.0, 1.0].",
            "Result (new OPEX) is always >= 0.0.",
        ],
        "deps": [
            "opex_base — from BU state.",
            "investment_ratio, synergy_multiplier — from round decisions / round_configs.py.",
        ],
        "edge_cases": [
            "investment_ratio = 0 → no change.",
            "investment_ratio = 1 → maximum reduction.",
            "synergy_multiplier > 1.0 → verify OPEX does not go negative.",
            "old_opex = 0 → return 0.",
        ],
    },
    {
        "id": "D.2.5",
        "name": "Natural Capital Cost of Debt",
        "file": "backend/engine.py",
        "functions": "calc_natural_capital_interest",
        "goal": (
            "Add a surcharge to the base interest rate proportional to the firm's Natural "
            "Capital Debt (NCD): rate = base_rate + NCD × 0.0001. Calibrated so NCD 500 ≈ 10 % "
            "and NCD 1 000 ≈ 15 %."
        ),
        "invariants": [
            "natural_capital_debt floored at 0 (no negative surcharge).",
            "Returned rate floored at base_rate.",
        ],
        "deps": [
            "base_rate — from round_configs.py.",
            "natural_capital_debt — accumulated in game state.",
        ],
        "edge_cases": [
            "NCD = 0 → rate equals base_rate.",
            "NCD < 0 → clamp to 0.",
            "Extreme NCD (e.g., 10 000) → verify rate does not overflow.",
        ],
    },
    {
        "id": "D.2.6",
        "name": "Burnout Accumulation Engine",
        "file": "backend/engine.py",
        "functions": "calc_burnout_accumulation",
        "goal": (
            "Track staff fatigue across 6-month rounds. Applies HR-driven delta plus natural "
            "drift (+6.0/round when no HR investment is made). OPEX penalty activates above "
            "burnout 20 via a quadratic curve; maximum ~18 % penalty at burnout 100."
        ),
        "invariants": [
            "new_burnout clamped to [0, 100].",
            "opex_penalty_rate is always >= 0.",
            "critical_burnout flag set when new_burnout > 70.",
        ],
        "deps": [
            "staff_burnout_index — per BU from game state.",
            "burnout_delta — from HR pillar decision.",
            "natural_drift — defaults to 6.0; set to 0 when HR invested this round.",
        ],
        "edge_cases": [
            "Burnout at 100 with positive delta → stays at 100.",
            "Burnout at 0 with negative delta → stays at 0.",
            "natural_drift = 0 when HR is invested.",
            "burnout = 20 → opex_penalty_rate = 0 (boundary check).",
        ],
    },
    {
        "id": "D.2.7",
        "name": "Workforce Readiness Engine",
        "file": "backend/engine.py",
        "functions": "calc_workforce_readiness",
        "goal": (
            "Track aggregate workforce competence across rounds. High HR: +16; Medium HR: +8; "
            "No investment: −10 (skills atrophy). Affects strategic pillar effectiveness and "
            "terminal valuation synergy bonus."
        ),
        "invariants": [
            "new_readiness clamped to [0, 100].",
            "low_readiness_penalty flag when < 40.",
            "high_readiness_bonus flag when > 75.",
        ],
        "deps": [
            "workforce_readiness — from game state (starts at 50).",
            "hr_quality_tier — from HR pillar decision ('high', 'medium', 'none').",
        ],
        "edge_cases": [
            "Starting readiness 0 + 'none' tier → stays at 0.",
            "Starting readiness 100 + 'high' tier → stays at 100.",
            "Unknown tier string → treated as 'none' (−10 delta).",
        ],
    },
    {
        "id": "D.2.8",
        "name": "Revenue Cannibalization Engine",
        "file": "backend/engine.py",
        "functions": "calc_revenue_cannibalization",
        "goal": (
            "Model intra-group market overlap: BUs with revenue >15 % above group average "
            "cannibalize overlapping BUs proportional to the _MARKET_OVERLAP matrix."
        ),
        "invariants": [
            "A BU cannot cannibalize itself.",
            "Cannibalization amounts are always >= 0.",
            "Penalty is additive across multiple aggressors.",
        ],
        "deps": [
            "bu_id, revenue_base — from bu_states.",
            "_MARKET_OVERLAP matrix — in engine.py.",
            "rate — defaults to 0.03.",
        ],
        "edge_cases": [
            "Single-BU game → no pairs → return {}.",
            "All revenues equal → no aggressor.",
            "Unknown BU pair → overlap defaults to 0.0.",
            "rate = 0 → no penalties.",
        ],
    },
    {
        "id": "D.2.9",
        "name": "Stakeholder Fatigue Engine",
        "file": "backend/engine.py",
        "functions": "calc_stakeholder_fatigue",
        "goal": (
            "Diminish trust recovery efficiency after repeated crises. "
            "efficiency = 1 / (1 + 0.3 × crisis_count). "
            "Stakeholders become progressively harder to appease."
        ),
        "invariants": [
            "efficiency is always > 0 (asymptote, never reaches 0).",
            "Effective recovery is always <= recovery_amount.",
        ],
        "deps": [
            "crisis_count_lifetime — accumulated in game state.",
            "recovery_amount — from stakeholder recovery decision.",
            "fatigue_factor — defaults to 0.3 (configurable).",
        ],
        "edge_cases": [
            "crisis_count = 0 → full recovery amount returned.",
            "recovery_amount = 0 → return 0.",
            "Large crisis_count (e.g., 100) → very small but non-zero effective recovery.",
        ],
    },
    {
        "id": "D.2.10",
        "name": "ESG Greenwashing Risk Engine",
        "file": "backend/engine.py",
        "functions": "calc_greenwashing_risk · check_bu_greenwash_scandal",
        "goal": (
            "Detect hypocrisy when players select high-impact green options (A/C) without "
            "backing them with sufficient investment ratios (>= 15 %). Triggers −15 reputation "
            "penalty and sets auditor tolerance to Hostile."
        ),
        "invariants": [
            "Scandal triggers only on option_a or option_c.",
            "Group-level penalty fixed at 15.0; moderate-choice penalty at 7.5.",
        ],
        "deps": [
            "choice — string from player decision.",
            "investment_ratio — per BU or per decision.",
            "green_investment_threshold — defaults to 0.15 in engine.py.",
        ],
        "edge_cases": [
            "Empty decisions list → avg_ratio = 0 → scandal triggers if green option selected.",
            "choice = 'option_b' → lenient 10 % threshold.",
            "All ratios >= 0.15 → no scandal.",
            "choice not in any known set → return (False, 0.0).",
        ],
    },
    {
        "id": "D.2.11",
        "name": "Macro Interest Rate Environment",
        "file": "backend/engine.py",
        "functions": "calc_macro_rate_environment",
        "goal": (
            "Model central bank policy cycles across 10 rounds: easing (R1–R2), neutral "
            "(R3–R5), tightening (R6–R8), crisis premium (R9–R10). Returns a Cost-of-Capital "
            "modifier and descriptive regime label."
        ),
        "invariants": [
            "Rate modifier is a finite float for all valid round_number values.",
            "Unknown round falls back to 0.0 modifier.",
        ],
        "deps": [
            "round_number — from game state.",
            "_MACRO_RATE_CYCLES — dict in engine.py.",
            "SIM_ROUNDS — from config.py.",
        ],
        "edge_cases": [
            "round_number = 0 → not in dict → returns 0.0 modifier.",
            "round_number > SIM_ROUNDS → returns 0.0 modifier.",
            "Negative round → same fallback.",
        ],
    },
]


# ── Registry rows ─────────────────────────────────────────────────────────────

_REGISTRY_ROWS = [
    ["1",  "Carbon Accounting Helpers",      "engine.py",               "get_scope_ratios, calc_revenue_weighted_avg_ci, apply_ci_delta_to_bus", "ECONOMIC_CARBON_PRICE_BASE, ECONOMIC_CARBON_PRICE_GROWTH"],
    ["2",  "Corporate Strategic Fund",       "engine.py",               "calc_csf",                             "SIM_INITIAL_BUDGET"],
    ["3",  "Contagion Engine",               "engine.py",               "calc_contagion",                       "—"],
    ["4",  "Synergy Engine",                 "engine.py",               "calc_synergy_opex",                    "—"],
    ["5",  "Natural Capital Cost of Debt",   "engine.py",               "calc_natural_capital_interest",        "—"],
    ["6",  "VRIO Decay",                     "engine.py",               "calc_vrio_decay",                      "—"],
    ["7",  "Burnout Accumulation",           "engine.py",               "calc_burnout_accumulation",            "—"],
    ["8",  "Workforce Readiness",            "engine.py",               "calc_workforce_readiness",             "—"],
    ["9",  "Talent Brain-Drain",             "engine.py",               "calc_talent_braindrain",               "—"],
    ["10", "Strike Probability",             "engine.py",               "calc_strike_probability",              "—"],
    ["11", "Natural Decay",                  "engine.py",               "apply_natural_decay",                  "—"],
    ["12", "Macroeconomic Inflation",        "engine.py",               "calc_inflation",                       "—"],
    ["13", "Execution Overrun Risk",         "engine.py",               "calc_overrun_risk",                    "—"],
    ["14", "Technical Debt",                 "engine.py",               "calc_technical_debt",                  "—"],
    ["15", "Revenue Cannibalization",        "engine.py",               "calc_revenue_cannibalization",         "—"],
    ["16", "Stakeholder Fatigue",            "engine.py",               "calc_stakeholder_fatigue",             "—"],
    ["17", "Supply Chain Contagion",         "engine.py",               "calc_supply_chain_contagion",          "—"],
    ["18", "Competitor Pressure",            "engine.py",               "calc_competitor_pressure",             "—"],
    ["19", "Cash Conversion",                "engine.py",               "calc_cash_conversion",                 "—"],
    ["20", "Dividend Ratchet",               "engine.py",               "calc_dividend_ratchet",                "—"],
    ["21", "Talent Allocation Pressure",     "engine.py",               "calc_talent_allocation_pressure",      "—"],
    ["22", "Technology Lock-In",             "engine.py",               "calc_technology_lockin",               "—"],
    ["23", "ESG Greenwashing Risk",          "engine.py",               "calc_greenwashing_risk, check_bu_greenwash_scandal", "—"],
    ["24", "Macro Interest Rate",            "engine.py",               "calc_macro_rate_environment",          "SIM_ROUNDS"],
    ["25", "Biodiversity Engine",            "biodiversity_engine.py",  "(see file)",                           "—"],
    ["26", "Balance Sheet Engine",           "balance_sheet.py",        "(see file)",                           "CONSTRAINT_MIN_LIQUIDITY_RATIO"],
    ["27", "Systemic Risk Engine",           "systemic_risk_engine.py", "(see file)",                           "CONSTRAINT_MAX_CARBON_EMISSIONS"],
    ["28", "Terminal Valuation",             "terminal_valuation.py",   "(see file)",                           "ECONOMIC_CIRCULAR_ECONOMY_BONUS"],
    ["29", "Regulatory Sandbox",             "regulatory_sandbox.py",   "(see file)",                           "—"],
    ["30", "Black Swan Registry",            "black_swan_registry.py",  "(see file)",                           "—"],
]


# ── Config reference rows ─────────────────────────────────────────────────────

_CONFIG_ROWS = [
    ["simulation_settings.rounds",               "SIM_ROUNDS",                        "10",         "rounds",    "Total 6-month simulation rounds"],
    ["simulation_settings.agents",               "SIM_AGENTS",                        "5",          "profiles",  "Number of player / BU profiles"],
    ["simulation_settings.initial_budget",       "SIM_INITIAL_BUDGET",                "50 000 000", "USD",       "Starting Corporate Strategic Fund"],
    ["economic_parameters.carbon_price_base",    "ECONOMIC_CARBON_PRICE_BASE",        "40.0",       "USD/tCO₂e", "Base carbon price"],
    ["economic_parameters.carbon_price_growth_rate", "ECONOMIC_CARBON_PRICE_GROWTH",  "0.15",       "rate",      "Annual carbon price escalation"],
    ["economic_parameters.circular_economy_efficiency_bonus", "ECONOMIC_CIRCULAR_ECONOMY_BONUS", "0.15", "ratio", "OPEX bonus from circular economy decisions"],
    ["constraints.max_carbon_emissions",         "CONSTRAINT_MAX_CARBON_EMISSIONS",   "5 000.0",    "tCO₂e",     "Group-wide emissions cap"],
    ["constraints.min_liquidity_ratio",          "CONSTRAINT_MIN_LIQUIDITY_RATIO",    "0.2",        "ratio",     "Minimum cash/assets ratio before penalty"],
]


# ── Validation checklist ──────────────────────────────────────────────────────

_VALIDATION_ITEMS = [
    "Blueprint entry completed — all four fields filled (System Goal, Logical Invariants, Data Dependencies, Edge Cases).",
    "Module added to the quick-reference registry table.",
    "New simulation_config.json keys documented in the Config Reference (if any).",
    "Edge-case tests added to backend/validation_logic.py.",
    "All invariants asserted in the test (clamping, sign correctness, empty-list guards).",
    "No magic numbers — all tuneable values sourced from config.py constants.",
    "blueprint.md committed in the same PR as the implementation.",
]


# ── Main builder ──────────────────────────────────────────────────────────────

def build_appendix_d(doc):
    """Append the full Architecture Blueprint as Appendix D."""
    add_page_break(doc)

    # ── Cover heading ──────────────────────────────────────────────────────────
    doc.add_heading("Appendix D: Architecture Blueprint — Module Design Standard", level=1)

    intro = doc.add_paragraph(
        "This appendix is the canonical reference for adding new logic modules to the "
        "Muressons simulation engine. Every new mechanic must complete the four-section "
        "blueprint before any code is merged, preventing logical drift, ensuring invariant "
        "coverage, and maintaining a single source of truth for all configurable parameters."
    )
    intro.paragraph_format.space_after = Pt(10)

    add_callout(
        doc,
        "This document mirrors blueprint.md in the repository root. "
        "Any update to blueprint.md must be reflected here before the next manual release.",
        style="important",
    )

    # ── D.1 Blueprint Template ─────────────────────────────────────────────────
    add_page_break(doc)
    doc.add_heading("D.1  Module Blueprint Template", level=2)
    doc.add_paragraph(
        "Copy the template below for every new module. All four sections are mandatory."
    )

    add_styled_table(
        doc,
        ["Section", "Description"],
        [
            ["System Goal",
             "Define the purpose of the new mechanic — what player behaviour or "
             "real-world system does it model?"],
            ["Logical Invariants",
             "Conditions that must remain true at all times (e.g., sum of assets = "
             "sum of liabilities + equity; scores clamped to [0, 100])."],
            ["Data Dependencies",
             "Parameters pulled from simulation_config.json via backend/config.py, "
             "and any BU-state fields that must be present in the game state dict."],
            ["Edge Cases",
             "Extreme or degenerate inputs to be tested in backend/validation_logic.py "
             "(e.g., empty BU list, zero revenue, round_number out of range)."],
        ],
        col_widths=[1.6, 5.4],
    )

    doc.add_paragraph()
    doc.add_paragraph("Fill-in template (copy verbatim):").runs[0].font.bold = True

    template_lines = [
        "Module: <Module Name>",
        "File:   backend/<filename>.py",
        "Added:  Round / Version <X>",
        "",
        "System Goal",
        "  What real-world mechanic does this module simulate?",
        "  What player decision does it respond to?",
        "",
        "Logical Invariants",
        "  - <invariant 1>",
        "  - <invariant 2>",
        "",
        "Data Dependencies",
        "  From simulation_config.json (via config.py):",
        "    SIM_ROUNDS, SIM_INITIAL_BUDGET, ECONOMIC_CARBON_PRICE_BASE, ...",
        "  From bu_states list:",
        "    bu_id, revenue_base, opex_base, carbon_intensity, ...",
        "",
        "Edge Cases (backend/validation_logic.py)",
        "  - Empty BU list (len == 0) → must return neutral/zero, not raise",
        "  - All revenues == 0 → fallback to simple mean",
        "  - crisis_severity < 0 → clamp to 0 before sigmoid",
        "  - investment_ratio > 1.0 → clamp to 1.0",
        "  - round_number outside [1, SIM_ROUNDS] → fallback to 0.0 modifier",
    ]
    for line in template_lines:
        _add_mono_para(doc, line)

    # ── D.2 Registered Modules ─────────────────────────────────────────────────
    add_page_break(doc)
    doc.add_heading("D.2  Registered Modules — Full Detail", level=2)
    doc.add_paragraph(
        "Each shipped logic module is documented below. Modules are ordered by engine layer. "
        "Eleven core engine.py functions are expanded in full; the remaining 19 are summarised "
        "in the registry table (§D.3)."
    )

    for mod in _MODULES:
        _add_section_rule(doc)

        # Module heading
        h = doc.add_heading(f"{mod['id']}  {mod['name']}", level=3)

        # File / functions meta
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.space_after = Pt(4)
        r1 = p.add_run("File: ")
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r2 = p.add_run(mod["file"] + "    ")
        r2.font.name = "Courier New"
        r2.font.size = Pt(9)
        r3 = p.add_run("Functions: ")
        r3.font.bold = True
        r3.font.size = Pt(9.5)
        r4 = p.add_run(mod["functions"])
        r4.font.name = "Courier New"
        r4.font.size = Pt(9)

        # Four-section table
        rows = [
            ["System Goal",         mod["goal"]],
            ["Logical Invariants",  "\n".join(f"• {i}" for i in mod["invariants"])],
            ["Data Dependencies",   "\n".join(f"• {d}" for d in mod["deps"])],
            ["Edge Cases",          "\n".join(f"• {e}" for e in mod["edge_cases"])],
        ]

        table = doc.add_table(rows=len(rows), cols=2)
        table.style = "Table Grid"
        col_widths = [Inches(1.55), Inches(5.45)]
        for ri, (label, content) in enumerate(rows):
            cells = table.rows[ri].cells
            # Label cell
            cells[0].text = label
            for p2 in cells[0].paragraphs:
                for r in p2.runs:
                    r.font.bold = True
                    r.font.size = Pt(9)
                    r.font.color.rgb = WHITE
            _shade_cell(cells[0], "0F172A")  # BRAND_NAVY hex
            cells[0].width = col_widths[0]
            # Content cell
            cells[1].text = content
            for p2 in cells[1].paragraphs:
                for r in p2.runs:
                    r.font.size = Pt(9)
            if ri % 2 == 1:
                _shade_cell(cells[1], "F3F4F6")  # LIGHT_GRAY hex
            cells[1].width = col_widths[1]

        doc.add_paragraph()

    # ── D.3 Module Registry ────────────────────────────────────────────────────
    add_page_break(doc)
    doc.add_heading("D.3  Module Registry — Quick Reference", level=2)
    doc.add_paragraph(
        "All 30 currently shipped logic modules. Use this table as the first-pass "
        "audit when adding a new module — ensure no duplication of responsibility."
    )

    add_styled_table(
        doc,
        ["#", "Module Name", "File", "Primary Function(s)", "Config Keys Used"],
        _REGISTRY_ROWS,
        col_widths=[0.25, 1.55, 1.45, 2.15, 1.6],
    )

    # ── D.4 Simulation Config Reference ───────────────────────────────────────
    add_page_break(doc)
    doc.add_heading("D.4  Simulation Config Reference", level=2)
    doc.add_paragraph(
        "All tuneable parameters live in simulation_config.json and are loaded into typed "
        "constants by backend/config.py. Never hardcode any value from this table directly "
        "in engine logic — always import the constant from config.py."
    )

    add_callout(
        doc,
        "Rule: If a value appears in this table, it must not be hardcoded anywhere in "
        "backend/engine.py, round_logic.py, or any other module. "
        "Import the config.py constant instead.",
        style="warning",
    )

    add_styled_table(
        doc,
        ["JSON Path", "Config Constant", "Default", "Unit", "Description"],
        _CONFIG_ROWS,
        col_widths=[1.9, 1.9, 0.7, 0.65, 2.05],
    )

    # ── D.5 Validation Checklist ───────────────────────────────────────────────
    add_page_break(doc)
    doc.add_heading("D.5  Validation Checklist — PR Gate", level=2)
    doc.add_paragraph(
        "Before merging any new logic module, every item below must be ticked. "
        "The PR reviewer is responsible for confirming completion."
    )

    for item in _VALIDATION_ITEMS:
        p = doc.add_paragraph(style="List Bullet")
        p.clear()
        r_box = p.add_run("☐  ")
        r_box.font.bold = True
        r_box.font.size = Pt(11)
        r_box.font.color.rgb = BRAND_TEAL
        r_text = p.add_run(item)
        r_text.font.size = Pt(10)

    doc.add_paragraph()
    add_callout(
        doc,
        "Merge without a complete blueprint entry constitutes a governance violation "
        "under the Muressons simulation integrity framework and may introduce logical drift "
        "that is extremely expensive to reverse post-deployment.",
        style="warning",
    )

    # ── D.6 How to Use ────────────────────────────────────────────────────────
    doc.add_heading("D.6  How to Use This Appendix", level=2)

    steps = [
        "Copy the template from §D.1 into a new section of blueprint.md.",
        "Fill in all four fields (System Goal, Logical Invariants, Data Dependencies, Edge Cases) before writing any code.",
        "Add a row to the registry table in §D.3.",
        "Register any new simulation_config.json keys in §D.4.",
        "Write edge-case tests in backend/validation_logic.py covering every item in your Edge Cases field.",
        "Commit blueprint.md alongside the implementation in the same PR.",
        "Update this appendix in the next Facilitator Manual release.",
    ]
    for i, step in enumerate(steps, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.2)
        p.paragraph_format.space_after = Pt(5)
        r_num = p.add_run(f"{i}.  ")
        r_num.font.bold = True
        r_num.font.size = Pt(10)
        r_num.font.color.rgb = BRAND_BLUE
        r_text = p.add_run(step)
        r_text.font.size = Pt(10)

    doc.add_paragraph()
    p_footer = doc.add_paragraph()
    r_f = p_footer.add_run(
        "Last updated: 2026-05-28  ·  Maintained by the Muressons simulation engineering team."
    )
    r_f.font.size = Pt(8.5)
    r_f.font.italic = True
    r_f.font.color.rgb = BRAND_GRAY
