"""
Muressons Simulation — Config Excel Converter
Bidirectional converter between simulation_config.json ↔ simulation_config.xlsx

Usage:
    python config_excel.py export   # JSON → Excel
    python config_excel.py import   # Excel → JSON

Dev dependency only — openpyxl is NOT required at simulation runtime.
"""

import json
import sys
from pathlib import Path
from typing import Any

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
    from openpyxl.utils import get_column_letter
except ImportError:
    print("ERROR: openpyxl is required. Install with: pip install openpyxl")
    sys.exit(1)

# ── Paths ────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
JSON_PATH  = _ROOT / "simulation_config.json"
EXCEL_PATH = _ROOT / "simulation_config.xlsx"

# ── Description Catalog ──────────────────────────────────────────
# Maps (section, subsection, parameter) → (unit, description)
_DESCRIPTIONS: dict[tuple[str, str, str], tuple[str, str]] = {
    # ── simulation_settings ──
    ("simulation_settings", "", "rounds"):                          ("rounds",    "Total number of simulation rounds per game"),
    ("simulation_settings", "", "agents"):                          ("count",     "Number of AI/NPC agents in the simulation"),
    ("simulation_settings", "", "initial_budget"):                  ("$",         "Starting corporate treasury for each team"),

    # ── economic_parameters ──
    ("economic_parameters", "", "carbon_price_base"):               ("$/tCO₂e",  "Base carbon price at round 1 (escalates per round)"),
    ("economic_parameters", "", "carbon_price_growth_rate"):        ("%/round",   "Carbon price escalation rate per 6-month round"),
    ("economic_parameters", "", "circular_economy_efficiency_bonus"): ("%",       "OPEX efficiency bonus for circular economy investments"),

    # ── constraints ──
    ("constraints", "", "max_carbon_emissions"):                    ("tCO₂e",    "Maximum allowable total carbon emissions before penalty"),
    ("constraints", "", "min_liquidity_ratio"):                     ("ratio",     "Minimum liquidity ratio before covenant breach"),

    # ── financial_parameters ──
    ("financial_parameters", "", "shadow_carbon_price"):            ("$/tCO₂e",  "Internal shadow carbon price for CAROIC calculation"),
    ("financial_parameters", "", "corporate_tax_rate"):             ("%",         "Corporate income tax rate (CAROIC, balance sheet, terminal val)"),
    ("financial_parameters", "", "free_csf_pct"):                   ("%",         "Fraction of treasury that is 'free' capital — CapEx below this requires no loan"),
    ("financial_parameters", "", "capex_cap_multiple"):             ("×",         "Max CapEx allowed per round as multiple of starting treasury"),
    ("financial_parameters", "", "emergency_credit_amount"):        ("$",         "Size of emergency credit facility for distressed teams"),
    ("financial_parameters", "", "default_loan_rate"):              ("%",         "Default loan interest rate when no event override is set"),
    ("financial_parameters", "", "emergency_rate_spread"):          ("%",         "Basis-point spread added for emergency credit facility"),
    ("financial_parameters", "", "insolvency_threshold"):           ("$",         "Treasury level below which mandatory austerity triggers"),
    ("financial_parameters", "", "treasury_floor"):                 ("$",         "Absolute hard floor on corporate treasury"),
    ("financial_parameters", "", "wacc_lender_threshold"):          ("%",         "ESG-WACC threshold above which lenders tighten covenants"),

    # ── ncd_parameters ──
    ("ncd_parameters", "", "hard_cap"):                             ("units",     "Absolute hard cap on Natural Capital Debt per BU"),
    ("ncd_parameters", "", "warn_threshold"):                       ("units",     "50%-of-cap warning — triggers credit downgrade narrative"),
    ("ncd_parameters", "", "opex_scaling_factor"):                  ("$/unit",    "Converts NCD units to OPEX penalty (× hostility multiplier)"),
    ("ncd_parameters", "", "provision_per_unit"):                   ("$/unit",    "Balance sheet environmental provision per unit of avg NCD"),
    ("ncd_parameters", "", "event_provision"):                      ("$",         "Fixed provision added per active remediation event (IAS 37)"),

    # ── climate_parameters ──
    ("climate_parameters", "", "loss_damage_levy_tipped"):          ("$",         "UNFCCC Loss & Damage levy when tipping tier = 'tipped'"),
    ("climate_parameters", "", "loss_damage_levy_stressed"):        ("$",         "UNFCCC Loss & Damage levy when tipping tier = 'stressed'"),

    # ── balance_sheet_parameters ──
    ("balance_sheet_parameters", "", "slo_capital_scaling"):        ("$/pt",      "Social Licence Capital = avg_slo × this (non-GAAP)"),
    ("balance_sheet_parameters", "", "rep_capital_scaling"):        ("$/pt",      "Reputation Capital = group_rep × this (non-GAAP)"),
    ("balance_sheet_parameters", "", "covenant_green_ratio"):       ("ratio",     "Net Debt / EBITDA ≤ this → covenant status 'green'"),

    # ── contagion_parameters ──
    ("contagion_parameters", "", "max_reputation_drop"):            ("pts",       "Max reputation eroded at crisis saturation (sigmoid → 1.0)"),
    ("contagion_parameters", "", "severity_midpoint"):              ("severity",  "Crisis severity at sigmoid inflection (50% of max drop)"),
    ("contagion_parameters", "", "steepness_factor"):               ("factor",    "Sigmoid steepness — smaller = steeper cliff-like response"),

    # ── npc_shock_parameters ──
    ("npc_shock_parameters", "", "npc_shock_base_prob"):            ("prob",      "Base probability anchor for all materiality shock events"),
    ("npc_shock_parameters", "", "npc_shock_max_prob"):             ("prob",      "Hard ceiling on any single materiality shock probability"),

    # ── engine_parameters.synergy ──
    ("engine_parameters", "synergy", "dampening_factor"):           ("factor",    "Diminishing returns dampening on synergy OPEX savings"),
    # ── engine_parameters.natural_capital ──
    ("engine_parameters", "natural_capital", "interest_coefficient"): ("rate/unit", "NCD interest rate surcharge coefficient per unit NCD"),
    # ── engine_parameters.natural_decay ──
    ("engine_parameters", "natural_decay", "factor"):               ("factor",    "6-month passive decay multiplier for reputation/SLO scores"),
    # ── engine_parameters.burnout ──
    ("engine_parameters", "burnout", "natural_drift"):              ("pts/round", "Default passive burnout drift per round (no HR investment)"),
    ("engine_parameters", "burnout", "opex_threshold"):             ("pts",       "Burnout level above which OPEX penalty activates"),
    ("engine_parameters", "burnout", "critical_threshold"):         ("pts",       "Burnout level classified as critical (amplified penalty)"),
    ("engine_parameters", "burnout", "opex_penalty_coeff"):         ("coeff",     "Quadratic coefficient for burnout → OPEX penalty curve"),
    ("engine_parameters", "burnout", "passive_decay_healthcare"):   ("pts/round", "Healthcare BU burnout passive recovery per round"),
    ("engine_parameters", "burnout", "passive_decay_default"):      ("pts/round", "Non-healthcare BU burnout passive recovery per round"),
    # ── engine_parameters.workforce_readiness ──
    ("engine_parameters", "workforce_readiness", "delta_high"):     ("pts",       "Readiness boost from high HR investment"),
    ("engine_parameters", "workforce_readiness", "delta_medium"):   ("pts",       "Readiness boost from medium HR investment"),
    ("engine_parameters", "workforce_readiness", "delta_none"):     ("pts",       "Readiness atrophy when no HR investment (negative)"),
    ("engine_parameters", "workforce_readiness", "low_threshold"):  ("pts",       "Below this readiness → OPEX penalty applied"),
    ("engine_parameters", "workforce_readiness", "high_threshold"): ("pts",       "Above this readiness → OPEX bonus applied"),
    # ── engine_parameters.talent_braindrain ──
    ("engine_parameters", "talent_braindrain", "reputation_threshold"): ("pts",   "Reputation below this triggers brain-drain OPEX penalty"),
    ("engine_parameters", "talent_braindrain", "penalty_multiplier"): ("×",       "OPEX penalty scaling multiplier for brain-drain"),
    ("engine_parameters", "talent_braindrain", "burnout_threshold"): ("pts",      "Burnout above this triggers additional overhead cost"),
    ("engine_parameters", "talent_braindrain", "burnout_overhead_factor"): ("×",   "Overhead scaling factor when burnout exceeds threshold"),
    # ── engine_parameters.overrun_risk ──
    ("engine_parameters", "overrun_risk", "capex_threshold"):       ("$",         "CapEx above this → overrun risk probability activates"),
    ("engine_parameters", "overrun_risk", "default_probability"):   ("prob",      "Default probability of a cost overrun occurring"),
    ("engine_parameters", "overrun_risk", "default_severity"):      ("%",         "Default overrun cost as fraction of CapEx"),
    # ── engine_parameters.technical_debt ──
    ("engine_parameters", "technical_debt", "rounds_threshold"):    ("rounds",    "Consecutive zero-invest rounds before tech debt penalty"),
    ("engine_parameters", "technical_debt", "penalty_rate"):        ("%",         "OPEX penalty rate for accumulated technical debt"),
    # ── engine_parameters.technology_lockin ──
    ("engine_parameters", "technology_lockin", "rounds_threshold"): ("rounds",    "Consecutive rounds for technology lock-in trigger"),
    ("engine_parameters", "technology_lockin", "penalty_rate"):     ("%",         "Synergy penalty rate when technology lock-in fires"),
    # ── engine_parameters.strike_probability ──
    ("engine_parameters", "strike_probability", "social_license_weight"): ("weight", "SLO deficit weight in strike probability calculation"),
    # ── engine_parameters.cannibalization ──
    ("engine_parameters", "cannibalization", "base_rate"):          ("%",         "Base revenue cannibalization rate between overlapping BUs"),
    ("engine_parameters", "cannibalization", "aggressor_threshold_multiplier"): ("×", "Revenue multiple above avg that triggers aggressor status"),
    # ── engine_parameters.dividend_ratchet ──
    ("engine_parameters", "dividend_ratchet", "rep_penalty"):       ("pts",       "Reputation penalty when dividends are cut"),
    ("engine_parameters", "dividend_ratchet", "cut_threshold"):     ("ratio",     "Dividend ratio below this vs. last round = 'cut'"),
    # ── engine_parameters.talent_allocation ──
    ("engine_parameters", "talent_allocation", "neglect_threshold"): ("%",        "CapEx share below this → talent neglect penalty"),
    ("engine_parameters", "talent_allocation", "penalty_rate"):     ("%",         "OPEX premium for talent neglect"),
    # ── engine_parameters.stakeholder_fatigue ──
    ("engine_parameters", "stakeholder_fatigue", "factor"):         ("factor",    "Trust recovery fatigue factor (higher = slower recovery)"),
    # ── engine_parameters.supply_chain ──
    ("engine_parameters", "supply_chain", "overlap_coefficient"):   ("rate",      "Supply chain governance contagion rate between BUs"),
    # ── engine_parameters.competitor ──
    ("engine_parameters", "competitor", "growth_rate"):             ("%/round",   "NPC competitor EBITDA growth rate per round"),
    # ── engine_parameters.greenwashing ──
    ("engine_parameters", "greenwashing", "investment_threshold"):  ("%",         "Min investment ratio to back a green claim credibly"),
    ("engine_parameters", "greenwashing", "slo_penalty"):           ("pts",       "SLO penalty per BU when greenwashing scandal fires"),
    ("engine_parameters", "greenwashing", "moderate_threshold_scale"): ("factor", "Scaling for moderate greenwash threshold"),
    ("engine_parameters", "greenwashing", "moderate_penalty_scale"): ("factor",   "Scaling for moderate greenwash penalty"),
    ("engine_parameters", "greenwashing", "bu_rep_penalty"):        ("pts",       "Per-BU reputation delta on greenwashing"),
    # ── engine_parameters.sbti_pathway ──
    ("engine_parameters", "sbti_pathway", "baseline_ci"):           ("tCO₂e/$M", "SBTi 1.5°C baseline carbon intensity target"),
    ("engine_parameters", "sbti_pathway", "annual_reduction_rate"): ("%/yr",      "SBTi required annual CI reduction rate (8.22%)"),
    ("engine_parameters", "sbti_pathway", "misalignment_rounds"):   ("rounds",    "Consecutive misaligned rounds before CoC surcharge"),
    ("engine_parameters", "sbti_pathway", "coc_surcharge"):         ("%",         "Cost of capital surcharge for SBTi misalignment"),
    ("engine_parameters", "sbti_pathway", "credibility_per_round"): ("pts",       "Credibility score increment per aligned round"),
    # ── engine_parameters.eu_taxonomy ──
    ("engine_parameters", "eu_taxonomy", "ci_threshold"):           ("tCO₂e/$M", "CI below this → BU revenue counts as taxonomy-aligned"),
    ("engine_parameters", "eu_taxonomy", "green_threshold_pct"):    ("%",         "Taxonomy alignment % above this → green finance discount"),
    ("engine_parameters", "eu_taxonomy", "brown_threshold_pct"):    ("%",         "Taxonomy alignment % below this → brown penalty"),
    ("engine_parameters", "eu_taxonomy", "coc_benefit"):            ("%",         "CoC benefit for exceeding green threshold (negative)"),
    ("engine_parameters", "eu_taxonomy", "coc_surcharge"):          ("%",         "CoC surcharge for falling below brown threshold"),
    # ── engine_parameters.cbam ──
    ("engine_parameters", "cbam", "ci_threshold"):                  ("tCO₂e/$M", "Average CI above this triggers CBAM border adjustment"),
    ("engine_parameters", "cbam", "scope12_fraction"):              ("ratio",     "Scope 1+2 ratio fraction for CBAM eligibility"),
    ("engine_parameters", "cbam", "surcharge_rate"):                ("$/tCO₂e",  "CBAM surcharge rate per tonne CO₂e"),
    # ── engine_parameters.regulatory_ratchet ──
    ("engine_parameters", "regulatory_ratchet", "baseline"):        ("pts",       "Starting governance risk baseline for regulatory fines"),
    ("engine_parameters", "regulatory_ratchet", "round_increment"): ("pts/2rnd",  "Baseline increment per 2 rounds (ratchet tightening)"),
    ("engine_parameters", "regulatory_ratchet", "fine_per_point"):  ("$/pt",      "Regulatory fine per governance risk point over baseline"),
    # ── engine_parameters.supplier_defection ──
    ("engine_parameters", "supplier_defection", "inv_threshold"):   ("%",         "Investment ratio below this + strict ESG → defection"),
    ("engine_parameters", "supplier_defection", "opex_multiplier"): ("×",         "OPEX shock multiplier on supplier defection (+10%)"),
    ("engine_parameters", "supplier_defection", "rev_multiplier"):  ("×",         "Revenue shock multiplier on supplier defection (-5%)"),
    # ── engine_parameters.cfo_austerity ──
    ("engine_parameters", "cfo_austerity", "loan_ratio_trigger"):   ("ratio",     "Loan-to-treasury ratio that triggers CFO austerity freeze"),
    # ── engine_parameters.cash_conversion ──
    ("engine_parameters", "cash_conversion", "gov_risk_divisor"):   ("divisor",   "Governance risk divisor in cash conversion efficiency"),
    ("engine_parameters", "cash_conversion", "efficiency_floor"):   ("ratio",     "Minimum cash conversion efficiency floor"),
    # ── engine_parameters.dso ──
    ("engine_parameters", "dso", "baseline_factor"):                ("%",         "DSO baseline deferred revenue factor"),
    ("engine_parameters", "dso", "gov_risk_scaling"):               ("rate",      "DSO scaling per unit of governance risk"),
    ("engine_parameters", "dso", "max_cap"):                        ("%",         "Maximum DSO cap as fraction of revenue"),
    # ── engine_parameters.macro_noise ──
    ("engine_parameters", "macro_noise", "inflation_band"):         ("±%",        "Inflation noise band per round (symmetric)"),
    ("engine_parameters", "macro_noise", "carbon_price_band"):      ("±%",        "Carbon price noise band per round (symmetric)"),
    ("engine_parameters", "macro_noise", "micro_strike_probability"): ("prob",    "Per-round probability of a micro-strike event"),
    ("engine_parameters", "macro_noise", "micro_strike_opex_rate"): ("%",         "OPEX penalty rate when micro-strike fires"),
    # ── engine_parameters.fx_risk ──
    ("engine_parameters", "fx_risk", "movement_band"):              ("±%",        "FX movement band per round (symmetric ±7%)"),
    ("engine_parameters", "fx_risk", "default_exposure"):           ("%",         "Default foreign revenue exposure for unlisted BUs"),
    # ── engine_parameters.emissions_breach ──
    ("engine_parameters", "emissions_breach", "rep_penalty"):       ("pts",       "Reputation penalty for carbon emissions breach"),
    # ── engine_parameters.stranded_assets ──
    ("engine_parameters", "stranded_assets", "ci_threshold"):       ("tCO₂e/$M", "CI above this → BU classified as stranded asset"),
    ("engine_parameters", "stranded_assets", "coc_surcharge"):      ("%",         "CoC surcharge for holding stranded assets (+1.5%)"),
    # ── engine_parameters.tipping_hostility ──
    ("engine_parameters", "tipping_hostility", "tipped_multiplier"): ("×",        "NCD hostility multiplier when tipping tier = 'tipped'"),
    ("engine_parameters", "tipping_hostility", "stressed_multiplier"): ("×",      "NCD hostility multiplier when tipping tier = 'stressed'"),
    ("engine_parameters", "tipping_hostility", "warning_multiplier"): ("×",       "NCD hostility multiplier when tipping tier = 'warning'"),
    # ── engine_parameters.ncd_forgiveness ──
    ("engine_parameters", "ncd_forgiveness", "log_coefficient"):    ("coeff",     "NCD forgiveness logarithmic scaling coefficient"),
    # ── engine_parameters.implementation_lag ──
    ("engine_parameters", "implementation_lag", "inv_threshold"):    ("%",         "Investment ratio threshold for synergy implementation lag"),
    # ── engine_parameters.employer_brand ──
    ("engine_parameters", "employer_brand", "penalty_threshold"):   ("pts",       "Employer brand score below this → OPEX penalty"),
    ("engine_parameters", "employer_brand", "max_penalty_rate"):    ("%",         "Max employer brand OPEX penalty rate"),
    # ── engine_parameters.patient_outcomes ──
    ("engine_parameters", "patient_outcomes", "baseline"):          ("pts",       "Patient outcomes score baseline for revenue modifier"),
    ("engine_parameters", "patient_outcomes", "divisor"):           ("divisor",   "Patient outcomes divisor in revenue modifier formula"),
    ("engine_parameters", "patient_outcomes", "modifier_min"):      ("×",         "Minimum patient outcomes revenue modifier"),
    ("engine_parameters", "patient_outcomes", "modifier_max"):      ("×",         "Maximum patient outcomes revenue modifier"),
    # ── engine_parameters.utilization ──
    ("engine_parameters", "utilization", "overload_threshold"):     ("%",         "Bed utilization above this → burnout increment"),
    ("engine_parameters", "utilization", "overload_burnout_increment"): ("pts",   "Burnout increment per round when utilization overloaded"),
    ("engine_parameters", "utilization", "drift_rate"):             ("%/round",   "Bed utilization natural drift rate toward 100%"),
    # ── engine_parameters.imitation_decay ──
    ("engine_parameters", "imitation_decay", "default_rate"):       ("%/round",   "Default VRIO imitation decay rate per round"),
    # ── engine_parameters.scoring (abbreviated — all share pattern) ──
    ("engine_parameters", "scoring", "severity_routine_ceiling"):   ("%",         "Treasury impact below this → classified as 'routine'"),
    ("engine_parameters", "scoring", "severity_noteworthy_ceiling"): ("%",        "Treasury impact below this → 'noteworthy'"),
    ("engine_parameters", "scoring", "severity_material_ceiling"):  ("%",         "Treasury impact below this → 'material'"),
    ("engine_parameters", "scoring", "sdg_grade_a_plus"):           ("pts",       "SDG weighted score ≥ this → grade A+"),
    ("engine_parameters", "scoring", "sdg_grade_a"):                ("pts",       "SDG weighted score ≥ this → grade A"),
    ("engine_parameters", "scoring", "sdg_grade_b"):                ("pts",       "SDG weighted score ≥ this → grade B"),
    ("engine_parameters", "scoring", "sdg_grade_c"):                ("pts",       "SDG weighted score ≥ this → grade C"),
    ("engine_parameters", "scoring", "sdg_grade_d"):                ("pts",       "SDG weighted score ≥ this → grade D"),
    ("engine_parameters", "scoring", "caroic_grade_a_plus"):        ("%",         "CAROIC ≥ this → grade A+"),
    ("engine_parameters", "scoring", "caroic_grade_a"):             ("%",         "CAROIC ≥ this → grade A"),
    ("engine_parameters", "scoring", "caroic_grade_b"):             ("%",         "CAROIC ≥ this → grade B"),
    ("engine_parameters", "scoring", "caroic_grade_c"):             ("%",         "CAROIC ≥ this → grade C"),
    ("engine_parameters", "scoring", "cri_weight_gov_risk"):        ("weight",    "Governance risk weight in Contagion Risk Index"),
    ("engine_parameters", "scoring", "cri_weight_slo_deficit"):     ("weight",    "SLO deficit weight in Contagion Risk Index"),
    ("engine_parameters", "scoring", "cri_weight_rep_deficit"):     ("weight",    "Reputation deficit weight in Contagion Risk Index"),
    ("engine_parameters", "scoring", "cri_weight_carbon"):          ("weight",    "Carbon intensity weight in Contagion Risk Index"),
    ("engine_parameters", "scoring", "cri_tier_low"):               ("pts",       "CRI below this → 'Low' risk label"),
    ("engine_parameters", "scoring", "cri_tier_moderate"):          ("pts",       "CRI below this → 'Moderate' risk label"),
    ("engine_parameters", "scoring", "cri_tier_high"):              ("pts",       "CRI below this → 'High' risk label"),
    ("engine_parameters", "scoring", "momentum_weight_treasury"):   ("weight",    "Treasury velocity weight in momentum score"),
    ("engine_parameters", "scoring", "momentum_weight_rep"):        ("weight",    "Reputation delta weight in momentum score"),
    ("engine_parameters", "scoring", "momentum_weight_ncd"):        ("weight",    "NCD delta weight in momentum score"),
    ("engine_parameters", "scoring", "momentum_high_threshold"):    ("pts",       "Momentum score above this → 'High Momentum' label"),
    ("engine_parameters", "scoring", "momentum_comeback_mr_bonus"): ("bonus",     "Market-relative bonus for 'Comeback Kid' momentum"),
    ("engine_parameters", "scoring", "momentum_treasury_norm"):     ("divisor",   "Treasury velocity normalization factor"),
    ("engine_parameters", "scoring", "momentum_rep_multiplier"):    ("×",         "Reputation delta multiplier in momentum score"),
    ("engine_parameters", "scoring", "momentum_ncd_multiplier"):    ("×",         "NCD delta multiplier in momentum score"),
    ("engine_parameters", "scoring", "insolvency_warning_rounds"):  ("rounds",    "Rounds of negative treasury before insolvency warning"),
    ("engine_parameters", "scoring", "time_to_impact_horizon"):     ("rounds",    "Forecast look-ahead horizon for time-to-impact"),
    ("engine_parameters", "scoring", "braindrain_rep_threshold"):   ("pts",       "Reputation below this → brain-drain warning in forecast"),
    ("engine_parameters", "scoring", "strike_warning_threshold"):   ("prob",      "Strike probability above this → warning"),
    ("engine_parameters", "scoring", "strike_critical_threshold"):  ("prob",      "Strike probability above this → critical"),
    ("engine_parameters", "scoring", "contagion_risk_warning_threshold"): ("pts",  "CRI above this → board reflection trigger"),
    ("engine_parameters", "scoring", "treasury_drop_reflection_pct"): ("%",       "Treasury drop above this % → board reflection trigger"),

    # ── climate_var_parameters ──
    ("climate_var_parameters", "", "cyclone_prob_base"):             ("prob",      "Base cyclone probability for Climate VaR physical risk"),
    ("climate_var_parameters", "", "cyclone_prob_tipped"):           ("prob",      "Cyclone probability when tipping tier = 'tipped'"),
    ("climate_var_parameters", "", "cyclone_prob_stressed"):         ("prob",      "Cyclone probability when tipping tier = 'stressed'"),
    ("climate_var_parameters", "", "cyclone_prob_warning"):          ("prob",      "Cyclone probability when tipping tier = 'warning'"),
    ("climate_var_parameters", "", "physical_damage_base"):          ("$",         "Physical VaR maximum damage exposure (base)"),
    ("climate_var_parameters", "", "tipping_ci_warning"):            ("tCO₂e/$M", "Avg CI above this → climate 'warning' tipping tier"),
    ("climate_var_parameters", "", "tipping_ci_stressed"):           ("tCO₂e/$M", "Avg CI above this → climate 'stressed' tipping tier"),
    ("climate_var_parameters", "", "tipping_ci_tipped"):             ("tCO₂e/$M", "Avg CI above this → irreversible 'tipped' tier"),
    ("climate_var_parameters", "", "transition_var_ci_threshold"):   ("tCO₂e/$M", "CI above this → BU revenue counts as stranded exposure"),
    ("climate_var_parameters", "", "transition_var_stranded_multiplier"): ("%",    "Stranded exposure VaR multiplier"),
    ("climate_var_parameters", "", "transition_var_fee_years"):      ("years",     "Carbon fee projection horizon for transition VaR"),

    # ── balance_sheet_accounting ──
    ("balance_sheet_accounting", "", "capex_capitalisation_rate"):   ("%",         "Fraction of CapEx capitalised as PPE (IAS 16)"),
    ("balance_sheet_accounting", "", "annual_depreciation_rate"):    ("%/yr",      "Straight-line annual depreciation rate"),
    ("balance_sheet_accounting", "", "brand_base_per_bu"):           ("$",         "Brand valuation base per business unit"),
    ("balance_sheet_accounting", "", "min_environmental_provision"): ("$",         "Minimum irreducible environmental provision (IAS 37)"),
    ("balance_sheet_accounting", "", "decommissioning_accretion_rate"): ("%/yr",   "Decommissioning provision accretion rate (IAS 37)"),

    # ── terminal_valuation ──
    ("terminal_valuation", "", "shares_outstanding"):               ("shares",    "Total shares outstanding for per-share valuation"),
    ("terminal_valuation", "", "ipo_price_per_share"):              ("$/share",   "IPO price per share (starting share price)"),
    ("terminal_valuation", "", "long_run_growth"):                  ("%/yr",      "Long-run perpetuity growth rate for DCF terminal value"),
    ("terminal_valuation", "", "exit_multiple_floor"):              ("×",         "Minimum exit EV/EBITDA multiple"),
    ("terminal_valuation", "", "exit_multiple_ceiling"):            ("×",         "Maximum exit EV/EBITDA multiple"),

    # ── black_swan_limits ──
    ("black_swan_limits", "", "max_event_probability"):             ("prob",      "Hard ceiling on any single black swan event probability"),

    # ── turnaround_pathway ──
    ("turnaround_pathway", "crisis", "entry_treasury"):             ("$",         "Treasury at or below this → crisis phase entry"),
    ("turnaround_pathway", "crisis", "entry_reputation"):           ("pts",       "Reputation at or below this → crisis phase entry"),
    ("turnaround_pathway", "crisis", "bailout"):                    ("$",         "Emergency bailout amount on crisis entry"),
    ("turnaround_pathway", "crisis", "capex_cap"):                  ("×",         "CapEx cap multiplier during crisis phase"),
    ("turnaround_pathway", "crisis", "mr_cap"):                     ("×",         "Market-relative performance cap during crisis"),
    ("turnaround_pathway", "stabilisation", "exit_treasury"):       ("$",         "Treasury above this → exit stabilisation phase"),
    ("turnaround_pathway", "stabilisation", "exit_reputation"):     ("pts",       "Reputation above this → exit stabilisation phase"),
    ("turnaround_pathway", "stabilisation", "capex_cap"):           ("×",         "CapEx cap multiplier during stabilisation"),
    ("turnaround_pathway", "stabilisation", "mr_cap"):              ("×",         "Market-relative cap during stabilisation"),
    ("turnaround_pathway", "recovery", "exit_treasury"):            ("$",         "Treasury above this → exit recovery phase"),
    ("turnaround_pathway", "recovery", "exit_reputation"):          ("pts",       "Reputation above this → exit recovery phase"),
    ("turnaround_pathway", "recovery", "capex_cap"):                ("×",         "CapEx cap multiplier during recovery"),
    ("turnaround_pathway", "recovery", "mr_cap"):                   ("×",         "Market-relative cap during recovery"),
    ("turnaround_pathway", "exit", "exit_treasury"):                ("$",         "Treasury above this → exit turnaround entirely"),
    ("turnaround_pathway", "exit", "exit_reputation"):              ("pts",       "Reputation above this → exit turnaround entirely"),
    ("turnaround_pathway", "exit", "mr_bonus"):                     ("bonus",     "Market-relative bonus awarded on turnaround completion"),
}

# ── Section Display Names & Colors ───────────────────────────────
_SECTION_COLORS: dict[str, str] = {
    "simulation_settings":      "1B4F72",
    "economic_parameters":      "1A5276",
    "constraints":              "154360",
    "financial_parameters":     "0E6655",
    "ncd_parameters":           "0B5345",
    "climate_parameters":       "784212",
    "balance_sheet_parameters": "6E2C00",
    "contagion_parameters":     "4A235A",
    "npc_shock_parameters":     "512E5F",
    "engine_parameters":        "1C2833",
    "climate_var_parameters":   "7B241C",
    "balance_sheet_accounting": "6C3483",
    "terminal_valuation":       "1F618D",
    "black_swan_limits":        "C0392B",
    "turnaround_pathway":       "27AE60",
}

_SECTION_LABELS: dict[str, str] = {
    "simulation_settings":      "📋 Simulation Settings",
    "economic_parameters":      "📈 Economic Parameters",
    "constraints":              "🚧 Constraints",
    "financial_parameters":     "💰 Financial Parameters",
    "ncd_parameters":           "🌿 Natural Capital Debt (NCD)",
    "climate_parameters":       "🌡️ Climate Parameters",
    "balance_sheet_parameters": "📊 Balance Sheet Parameters",
    "contagion_parameters":     "🔗 Contagion Engine",
    "npc_shock_parameters":     "💥 NPC Materiality Shocks",
    "engine_parameters":        "⚙️ Engine Parameters",
    "climate_var_parameters":   "🌪️ Climate Value-at-Risk",
    "balance_sheet_accounting": "🧮 Balance Sheet Accounting",
    "terminal_valuation":       "🏦 Terminal Valuation",
    "black_swan_limits":        "🦢 Black Swan Limits",
    "turnaround_pathway":       "🔄 Turnaround Pathway",
}


# ═══════════════════════════════════════════════════════════════
#  EXPORT: JSON → Excel
# ═══════════════════════════════════════════════════════════════

def _flatten_config(config: dict) -> list[dict]:
    """Flatten nested JSON config into row dicts for the spreadsheet."""
    rows = []
    for section, section_val in config.items():
        if not isinstance(section_val, dict):
            continue
        # Check if this is a 2-level nested section (engine_parameters, turnaround_pathway)
        has_nested = any(isinstance(v, dict) for v in section_val.values())
        if has_nested:
            for subsection, sub_val in section_val.items():
                if subsection.startswith("_"):
                    continue  # skip _comment fields
                if isinstance(sub_val, dict):
                    for param, value in sub_val.items():
                        if param.startswith("_"):
                            continue
                        rows.append({
                            "section": section,
                            "subsection": subsection,
                            "parameter": param,
                            "value": value,
                        })
                else:
                    # Direct value in a mixed section
                    rows.append({
                        "section": section,
                        "subsection": "",
                        "parameter": subsection,
                        "value": sub_val,
                    })
        else:
            for param, value in section_val.items():
                if param.startswith("_"):
                    continue
                rows.append({
                    "section": section,
                    "subsection": "",
                    "parameter": param,
                    "value": value,
                })
    return rows


def _type_label(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "string"
    return str(type(value).__name__)


def export_to_excel(json_path: Path = JSON_PATH, excel_path: Path = EXCEL_PATH) -> None:
    """Read simulation_config.json and write a richly formatted Excel file."""
    with open(json_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    rows = _flatten_config(config)
    wb = Workbook()
    ws = wb.active
    ws.title = "Simulation Config"

    # ── Styles ────────────────────────────────────────────────
    header_font   = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill   = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
    header_align  = Alignment(horizontal="center", vertical="center", wrap_text=True)
    section_font  = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font     = Font(name="Calibri", size=10)
    param_font    = Font(name="Consolas", size=10)
    value_font    = Font(name="Calibri", size=10, bold=True)
    desc_font     = Font(name="Calibri", size=9, italic=True, color="555555")
    thin_border   = Border(
        bottom=Side(style="thin", color="D5D8DC"),
    )
    row_fill_even = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
    row_fill_odd  = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    # ── Headers ───────────────────────────────────────────────
    headers = ["Section", "Subsection", "Parameter", "Value", "Type", "Unit", "Description"]
    col_widths = [28, 22, 35, 18, 8, 12, 60]
    for col_idx, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = header_align
        cell.border    = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:G{len(rows) + 50}"

    # ── Data Rows ─────────────────────────────────────────────
    current_section = ""
    data_row = 1  # tracks alternating row color within a section
    row_num = 2

    for row_data in rows:
        section    = row_data["section"]
        subsection = row_data["subsection"]
        parameter  = row_data["parameter"]
        value      = row_data["value"]
        type_label = _type_label(value)

        # Insert section header row
        if section != current_section:
            current_section = section
            data_row = 0
            label = _SECTION_LABELS.get(section, section.replace("_", " ").title())
            color = _SECTION_COLORS.get(section, "2C3E50")
            section_fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
            for col_idx in range(1, 8):
                cell = ws.cell(row=row_num, column=col_idx)
                cell.fill = section_fill
                cell.font = section_font
                cell.alignment = Alignment(vertical="center")
                cell.border = thin_border
            ws.cell(row=row_num, column=1, value=label)
            ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=7)
            row_num += 1

        # Look up description
        desc_key = (section, subsection, parameter)
        unit, description = _DESCRIPTIONS.get(desc_key, ("", ""))

        # Alternating row color
        fill = row_fill_even if data_row % 2 == 0 else row_fill_odd
        data_row += 1

        # Write cells
        display_section = _SECTION_LABELS.get(section, section).lstrip("📋📈🚧💰🌿🌡️📊🔗💥⚙️🌪️🧮🏦🦢🔄 ")

        cells_data = [
            (display_section, data_font),
            (subsection, data_font),
            (parameter, param_font),
            (value, value_font),
            (type_label, data_font),
            (unit, data_font),
            (description, desc_font),
        ]
        for col_idx, (cell_value, font) in enumerate(cells_data, 1):
            cell = ws.cell(row=row_num, column=col_idx, value=cell_value)
            cell.font      = font
            cell.fill      = fill
            cell.alignment = Alignment(vertical="center", wrap_text=(col_idx == 7))
            cell.border    = thin_border

        row_num += 1

    # ── Print settings ────────────────────────────────────────
    ws.sheet_properties.tabColor = "2C3E50"

    wb.save(str(excel_path))
    print(f"[OK] Exported {len(rows)} parameters to: {excel_path}")


# ═══════════════════════════════════════════════════════════════
#  IMPORT: Excel → JSON
# ═══════════════════════════════════════════════════════════════

def _cast_value(value: Any, type_label: str) -> Any:
    """Cast an Excel cell value back to the correct Python type."""
    if type_label == "bool":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("true", "1", "yes")
    elif type_label == "int":
        return int(float(value))
    elif type_label == "float":
        return float(value)
    elif type_label == "string":
        return str(value)
    # Fallback: try to preserve the original type
    if isinstance(value, float) and value == int(value):
        return int(value)
    return value


def import_from_excel(excel_path: Path = EXCEL_PATH, json_path: Path = JSON_PATH) -> None:
    """Read simulation_config.xlsx and write simulation_config.json."""
    wb = load_workbook(str(excel_path), read_only=True, data_only=True)
    ws = wb.active

    config: dict[str, Any] = {}

    for row in ws.iter_rows(min_row=2, values_only=True):
        if row is None or all(cell is None for cell in row):
            continue

        section_raw, subsection, parameter, value, type_label, *_ = (
            list(row) + [None] * 7
        )[:7]

        # Skip section header rows (merged cells with emoji labels)
        if parameter is None or str(parameter).strip() == "":
            continue
        if section_raw is None or str(section_raw).strip() == "":
            continue

        section_raw = str(section_raw).strip()
        parameter   = str(parameter).strip()
        subsection  = str(subsection).strip() if subsection else ""
        type_label  = str(type_label).strip() if type_label else ""

        # Reverse-map display label → JSON key
        section_key = section_raw
        for json_key, label in _SECTION_LABELS.items():
            clean_label = label.lstrip("📋📈🚧💰🌿🌡️📊🔗💥⚙️🌪️🧮🏦🦢🔄 ")
            if section_raw == clean_label or section_raw == label:
                section_key = json_key
                break

        # Cast value
        if value is not None and type_label:
            value = _cast_value(value, type_label)

        # Build nested structure
        if subsection:
            config.setdefault(section_key, {}).setdefault(subsection, {})[parameter] = value
        else:
            config.setdefault(section_key, {})[parameter] = value

    # Preserve _comment fields from original JSON if it exists
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                original = json.load(f)
            for section, section_val in original.items():
                if isinstance(section_val, dict):
                    for key, val in section_val.items():
                        if key.startswith("_") and section in config:
                            config[section][key] = val
        except Exception:
            pass

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")

    param_count = sum(
        len(v) if not any(isinstance(vv, dict) for vv in v.values()) else
        sum(len(vv) for vv in v.values() if isinstance(vv, dict))
        for v in config.values() if isinstance(v, dict)
    )
    print(f"[OK] Imported {param_count} parameters to: {json_path}")


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Usage: python config_excel.py [export|import]")
        print("  export  — Generate Excel from simulation_config.json")
        print("  import  — Generate JSON from simulation_config.xlsx")
        sys.exit(1)

    command = sys.argv[1].lower()
    if command == "export":
        export_to_excel()
    elif command == "import":
        import_from_excel()
    else:
        print(f"Unknown command: {command}")
        print("Use 'export' or 'import'")
        sys.exit(1)


if __name__ == "__main__":
    main()
