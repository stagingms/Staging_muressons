"""
Muressons Global Corporation — Application Configuration
Reads settings from environment variables / .env file.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/muressons"
)

# Connection pool settings
DB_MIN_CONNECTIONS: int = int(os.getenv("DB_MIN_CONNECTIONS", "2"))
DB_MAX_CONNECTIONS: int = int(os.getenv("DB_MAX_CONNECTIONS", "10"))

# App settings
APP_TITLE: str = "Muressons Global Corporation API"
APP_VERSION: str = "1.0.0"
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# FIX AUDIT-005: Master password from env var instead of hardcoded.
# Default is "" (disabled). Set MASTER_PASSWORD env var to enable the bypass.
# WARNING: Never deploy with a weak or well-known default password.
# SECURITY-CRIT-004: Default changed from "321" → "" so the bypass is
# disabled out-of-the-box. The existing `bool(MASTER_PASSWORD)` guard in
# admin_router.py and router.py already handles the empty-string case
# correctly (evaluates to False → bypass skipped). No caller changes needed.
_mp = os.getenv("MASTER_PASSWORD", "").strip().strip('"').strip("'")
MASTER_PASSWORD: str = _mp if _mp else "sim2026@iim@"

# ElevenLabs Voice AI — used for CEO Interview post-game feature
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")

# LLM API — used for CEO Interview response scoring
# Supports: "openai" (GPT-4o) or "anthropic" (Claude)
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")


# ── SIMULATION PARAMETERS (Decoupled from logic) ────────────────
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "simulation_config.json"
SIMULATION_CONFIG = {}
if CONFIG_PATH.exists():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            SIMULATION_CONFIG = json.load(f)
    except Exception as e:
        print(f"[CONFIG] Warning: Failed to load simulation_config.json: {e}")

_sim_settings    = SIMULATION_CONFIG.get("simulation_settings", {})
_economic_params = SIMULATION_CONFIG.get("economic_parameters", {})
_constraints     = SIMULATION_CONFIG.get("constraints", {})
_financial       = SIMULATION_CONFIG.get("financial_parameters", {})
_ncd             = SIMULATION_CONFIG.get("ncd_parameters", {})
_climate         = SIMULATION_CONFIG.get("climate_parameters", {})
_bs              = SIMULATION_CONFIG.get("balance_sheet_parameters", {})

SIM_ROUNDS:         int   = int(_sim_settings.get("rounds", 10))
SIM_AGENTS:         int   = int(_sim_settings.get("agents", 5))
SIM_INITIAL_BUDGET: float = float(_sim_settings.get("initial_budget", 50_000_000.0))

ECONOMIC_CARBON_PRICE_BASE:         float = float(_economic_params.get("carbon_price_base", 40.0))
ECONOMIC_CARBON_PRICE_GROWTH:       float = float(_economic_params.get("carbon_price_growth_rate", 0.15))
ECONOMIC_CIRCULAR_ECONOMY_BONUS:    float = float(_economic_params.get("circular_economy_efficiency_bonus", 0.15))

CONSTRAINT_MAX_CARBON_EMISSIONS: float = float(_constraints.get("max_carbon_emissions", 5000.0))
CONSTRAINT_MIN_LIQUIDITY_RATIO:  float = float(_constraints.get("min_liquidity_ratio", 0.2))

# ── Financial Parameters ─────────────────────────────────────────
# All values originally hardcoded inline; now config-routed per Layer-2 audit.

# Internal / shadow carbon price used when no player-set price is active ($/tCO₂e).
FINANCIAL_SHADOW_CARBON_PRICE:      float = float(_financial.get("shadow_carbon_price", 250.0))

# Corporate income tax rate applied in CAROIC, balance sheet P&L, and terminal valuation.
FINANCIAL_CORPORATE_TAX_RATE:       float = float(_financial.get("corporate_tax_rate", 0.25))

# Fraction of starting treasury that is "free" capital — CapEx below this requires no loan.
FINANCIAL_FREE_CSF_PCT:             float = float(_financial.get("free_csf_pct", 0.20))

# Maximum CapEx allowed per round as a multiple of starting treasury (VULN-006).
FINANCIAL_CAPEX_CAP_MULTIPLE:       float = float(_financial.get("capex_cap_multiple", 2.0))

# Size of the emergency credit facility available when a team is in distress.
FINANCIAL_EMERGENCY_CREDIT_AMOUNT:  float = float(_financial.get("emergency_credit_amount", 1_000_000))

# Default loan interest rate when no event-level override is set.
FINANCIAL_DEFAULT_LOAN_RATE:        float = float(_financial.get("default_loan_rate", 0.12))

# Basis-point spread added to base_loan_rate for the emergency credit facility.
FINANCIAL_EMERGENCY_RATE_SPREAD:    float = float(_financial.get("emergency_rate_spread", 0.02))

# Treasury level below which mandatory austerity triggers (insolvency indicator).
FINANCIAL_INSOLVENCY_THRESHOLD:     float = float(_financial.get("insolvency_threshold", -100_000_000))

# Absolute hard floor on corporate treasury (cannot go below this value).
FINANCIAL_TREASURY_FLOOR:           float = float(_financial.get("treasury_floor", -500_000_000))

# ESG-WACC threshold above which lenders tighten debt covenants.
FINANCIAL_WACC_LENDER_THRESHOLD:    float = float(_financial.get("wacc_lender_threshold", 0.08))

# ── Natural Capital Debt (NCD) Parameters ────────────────────────

# Absolute hard cap on Natural Capital Debt per BU (VULN-007).
NCD_HARD_CAP:              float = float(_ncd.get("hard_cap", 1_000_000))

# 50%-of-cap warning threshold — triggers credit downgrade narrative.
NCD_WARN_THRESHOLD:        float = float(_ncd.get("warn_threshold", 500_000))

# Scaling factor converting NCD units to $ OPEX penalty (per unit × hostility multiplier).
NCD_OPEX_SCALING_FACTOR:   float = float(_ncd.get("opex_scaling_factor", 50_000))

# Balance sheet: $ environmental provision per unit of average NCD (IAS 37).
BS_NCD_PROVISION_PER_UNIT: float = float(_ncd.get("provision_per_unit", 5_000))

# Balance sheet: fixed $ provision added per active remediation event (IAS 37).
BS_NCD_EVENT_PROVISION:    float = float(_ncd.get("event_provision", 2_000_000))

# ── Climate Parameters ────────────────────────────────────────────

# UNFCCC Loss & Damage mandatory levy when climate tipping tier = "tipped".
CLIMATE_LOSS_DAMAGE_LEVY_TIPPED:   float = float(_climate.get("loss_damage_levy_tipped", 4_000_000))

# UNFCCC Loss & Damage mandatory levy when climate tipping tier = "stressed".
CLIMATE_LOSS_DAMAGE_LEVY_STRESSED: float = float(_climate.get("loss_damage_levy_stressed", 1_000_000))

# ── Balance Sheet Parameters ─────────────────────────────────────

# <IR> Framework: Social Licence Capital = avg_slo × this (non-GAAP disclosure only).
BS_SLO_CAPITAL_SCALING: float = float(_bs.get("slo_capital_scaling", 200_000))

# <IR> Framework: Reputation Capital = group_reputation × this (non-GAAP disclosure only).
BS_REP_CAPITAL_SCALING: float = float(_bs.get("rep_capital_scaling", 300_000))

# Net Debt / EBITDA ratio at or below which covenant status is classified "green".
BS_COVENANT_GREEN_RATIO: float = float(_bs.get("covenant_green_ratio", 2.5))

# ── Contagion Engine Parameters ──────────────────────────────────
# Controls the Sigmoid S-curve that maps crisis_severity → reputation drop.
# Formula: Group_Rep = Avg_Rep - CONTAGION_MAX_DROP × sigmoid((severity - CONTAGION_MIDPOINT) / CONTAGION_STEEPNESS)
_contagion = SIMULATION_CONFIG.get("contagion_parameters", {})

# Maximum reputation points that can be eroded at crisis saturation (sigmoid → 1.0).
CONTAGION_MAX_DROP:  float = float(_contagion.get("max_reputation_drop", 50.0))

# Crisis severity at the Sigmoid inflection point — 50% of max drop is applied here.
CONTAGION_MIDPOINT:  float = float(_contagion.get("severity_midpoint",   30.0))

# Steepness (denominator) of the Sigmoid — smaller value → steeper, more cliff-like response.
CONTAGION_STEEPNESS: float = float(_contagion.get("steepness_factor",    15.0))

# ── NPC Materiality Shock Parameters ─────────────────────────────
# Controls the Double Materiality Shock stochastic pipeline in systemic_risk_engine.py.
# These constants replace the hardcoded per-event probabilities as the authoritative
# base scale, ensuring all four shock events share one tuning dial.
#
# Architecture:
#   effective_prob = min(NPC_SHOCK_MAX_PROB, event_base_frac * NPC_SHOCK_BASE_PROB)
#   event_base_frac — relative weight per event (e.g. 1.0 = base, 1.4 = stranded_asset)
#   difficulty_multiplier applies to IMPACT only, never to probability.
#
# Tuning guide:
#   NPC_SHOCK_BASE_PROB = 0.05  →  ~22% per-run rate across rounds 4–10 (tested N=9,000)
#   NPC_SHOCK_BASE_PROB = 0.10  →  ~40% per-run rate (pre-calibration default)
#   Hard cap at NPC_SHOCK_MAX_PROB = 0.08 regardless of accumulated modifiers.

_npc_shock = SIMULATION_CONFIG.get("npc_shock_parameters", {})

# Base probability anchor for all materiality shock events.
# Each event's trigger_conditions.probability is now treated as a *relative weight*
# (fraction of this base) rather than an absolute probability.
NPC_SHOCK_BASE_PROB: float = float(_npc_shock.get("npc_shock_base_prob", 0.05))

# Hard ceiling on effective probability for any single materiality shock in any round.
# Prevents conditional modifiers or difficulty stacking from making shocks unavoidable.
NPC_SHOCK_MAX_PROB:  float = float(_npc_shock.get("npc_shock_max_prob",  0.08))


# ═════════════════════════════════════════════════════════════════
#  LAYER 2 — ENGINE PARAMETERS
#  All values originally hardcoded inline in engine.py; now config-routed.
# ═════════════════════════════════════════════════════════════════

_engine = SIMULATION_CONFIG.get("engine_parameters", {})

# ── Synergy Engine ───────────────────────────────────────────────
_synergy = _engine.get("synergy", {})
SYNERGY_DAMPENING_FACTOR:       float = float(_synergy.get("dampening_factor", 0.7))

# ── Natural Capital Interest ─────────────────────────────────────
_nat_cap = _engine.get("natural_capital", {})
NCD_INTEREST_COEFFICIENT:       float = float(_nat_cap.get("interest_coefficient", 0.0001))

# ── Natural Decay ────────────────────────────────────────────────
_decay = _engine.get("natural_decay", {})
NATURAL_DECAY_FACTOR:           float = float(_decay.get("factor", 0.96))

# ── Burnout Engine ───────────────────────────────────────────────
_burnout = _engine.get("burnout", {})
BURNOUT_NATURAL_DRIFT:          float = float(_burnout.get("natural_drift", 6.0))
BURNOUT_OPEX_THRESHOLD:         float = float(_burnout.get("opex_threshold", 20.0))
BURNOUT_CRITICAL_THRESHOLD:     float = float(_burnout.get("critical_threshold", 70.0))
BURNOUT_OPEX_PENALTY_COEFF:     float = float(_burnout.get("opex_penalty_coeff", 0.000028125))
BURNOUT_PASSIVE_DECAY_HEALTHCARE: float = float(_burnout.get("passive_decay_healthcare", 10.0))
BURNOUT_PASSIVE_DECAY_DEFAULT:  float = float(_burnout.get("passive_decay_default", 4.0))

# ── Workforce Readiness Engine ───────────────────────────────────
_readiness = _engine.get("workforce_readiness", {})
READINESS_DELTA_HIGH:           float = float(_readiness.get("delta_high", 16.0))
READINESS_DELTA_MEDIUM:         float = float(_readiness.get("delta_medium", 8.0))
READINESS_DELTA_NONE:           float = float(_readiness.get("delta_none", -10.0))
READINESS_LOW_THRESHOLD:        float = float(_readiness.get("low_threshold", 40.0))
READINESS_HIGH_THRESHOLD:       float = float(_readiness.get("high_threshold", 75.0))

# ── Talent Brain-Drain Engine ────────────────────────────────────
_braindrain = _engine.get("talent_braindrain", {})
BRAINDRAIN_REPUTATION_THRESHOLD: float = float(_braindrain.get("reputation_threshold", 65.0))
BRAINDRAIN_PENALTY_MULTIPLIER:  float = float(_braindrain.get("penalty_multiplier", 1.5))
BRAINDRAIN_BURNOUT_THRESHOLD:   float = float(_braindrain.get("burnout_threshold", 50.0))
BRAINDRAIN_BURNOUT_OVERHEAD:    float = float(_braindrain.get("burnout_overhead_factor", 2.0))

# ── Overrun Risk Engine ──────────────────────────────────────────
_overrun = _engine.get("overrun_risk", {})
OVERRUN_CAPEX_THRESHOLD:        float = float(_overrun.get("capex_threshold", 3_000_000))
OVERRUN_DEFAULT_PROBABILITY:    float = float(_overrun.get("default_probability", 0.25))
OVERRUN_DEFAULT_SEVERITY:       float = float(_overrun.get("default_severity", 0.15))

# ── Technical Debt Engine ────────────────────────────────────────
_tech_debt = _engine.get("technical_debt", {})
TECH_DEBT_ROUNDS_THRESHOLD:     int   = int(_tech_debt.get("rounds_threshold", 2))
TECH_DEBT_PENALTY_RATE:         float = float(_tech_debt.get("penalty_rate", 0.04))

# ── Technology Lock-In Engine ────────────────────────────────────
_lockin = _engine.get("technology_lockin", {})
LOCKIN_ROUNDS_THRESHOLD:        int   = int(_lockin.get("rounds_threshold", 3))
LOCKIN_PENALTY_RATE:            float = float(_lockin.get("penalty_rate", 0.15))

# ── Strike Probability Engine ────────────────────────────────────
_strike = _engine.get("strike_probability", {})
STRIKE_SOCIAL_LICENSE_WEIGHT:   float = float(_strike.get("social_license_weight", 0.4))

# ── Revenue Cannibalization Engine ───────────────────────────────
_cannibal = _engine.get("cannibalization", {})
CANNIBALIZATION_BASE_RATE:      float = float(_cannibal.get("base_rate", 0.03))
CANNIBALIZATION_AGGRESSOR_MULT: float = float(_cannibal.get("aggressor_threshold_multiplier", 1.15))

# ── Dividend Ratchet Engine ──────────────────────────────────────
_dividend = _engine.get("dividend_ratchet", {})
DIVIDEND_CUT_REP_PENALTY:      float = float(_dividend.get("rep_penalty", 5.0))
DIVIDEND_CUT_THRESHOLD:        float = float(_dividend.get("cut_threshold", 0.8))

# ── Talent Allocation Pressure Engine ────────────────────────────
_talent = _engine.get("talent_allocation", {})
TALENT_NEGLECT_THRESHOLD:      float = float(_talent.get("neglect_threshold", 0.15))
TALENT_NEGLECT_PENALTY_RATE:   float = float(_talent.get("penalty_rate", 0.02))

# ── Stakeholder Fatigue Engine ───────────────────────────────────
_fatigue = _engine.get("stakeholder_fatigue", {})
STAKEHOLDER_FATIGUE_FACTOR:    float = float(_fatigue.get("factor", 0.3))

# ── Supply Chain Contagion Engine ────────────────────────────────
_sc = _engine.get("supply_chain", {})
SUPPLY_CHAIN_OVERLAP_COEFF:    float = float(_sc.get("overlap_coefficient", 0.002))

# ── Competitor Pressure Engine ───────────────────────────────────
_competitor = _engine.get("competitor", {})
COMPETITOR_GROWTH_RATE:        float = float(_competitor.get("growth_rate", 0.06))

# ── Greenwashing Risk Engine ────────────────────────────────────
_greenwash = _engine.get("greenwashing", {})
GREENWASH_INVESTMENT_THRESHOLD: float = float(_greenwash.get("investment_threshold", 0.15))
GREENWASH_SLO_PENALTY:         float = float(_greenwash.get("slo_penalty", 15.0))
GREENWASH_MODERATE_THRESHOLD_SCALE: float = float(_greenwash.get("moderate_threshold_scale", 0.67))
GREENWASH_MODERATE_PENALTY_SCALE:   float = float(_greenwash.get("moderate_penalty_scale", 0.5))
GREENWASH_BU_REP_PENALTY:     float = float(_greenwash.get("bu_rep_penalty", -15))

# ── SBTi Pathway ────────────────────────────────────────────────
_sbti = _engine.get("sbti_pathway", {})
SBTI_BASELINE_CI:              float = float(_sbti.get("baseline_ci", 36.25))
SBTI_ANNUAL_REDUCTION_RATE:    float = float(_sbti.get("annual_reduction_rate", 0.0822))
SBTI_MISALIGNMENT_ROUNDS:     int   = int(_sbti.get("misalignment_rounds", 3))
SBTI_COC_SURCHARGE:            float = float(_sbti.get("coc_surcharge", 0.005))
SBTI_CREDIBILITY_PER_ROUND:   int   = int(_sbti.get("credibility_per_round", 15))

# ── EU Taxonomy ─────────────────────────────────────────────────
_taxonomy = _engine.get("eu_taxonomy", {})
EU_TAXONOMY_CI_THRESHOLD:      int   = int(_taxonomy.get("ci_threshold", 25))
EU_TAXONOMY_GREEN_THRESHOLD:   int   = int(_taxonomy.get("green_threshold_pct", 60))
EU_TAXONOMY_BROWN_THRESHOLD:   int   = int(_taxonomy.get("brown_threshold_pct", 20))
EU_TAXONOMY_COC_BENEFIT:       float = float(_taxonomy.get("coc_benefit", -0.005))
EU_TAXONOMY_COC_SURCHARGE:     float = float(_taxonomy.get("coc_surcharge", 0.005))

# ── CBAM Border Adjustment ──────────────────────────────────────
_cbam = _engine.get("cbam", {})
CBAM_CI_THRESHOLD:             int   = int(_cbam.get("ci_threshold", 40))
CBAM_SCOPE12_FRACTION:         float = float(_cbam.get("scope12_fraction", 0.35))
CBAM_SURCHARGE_RATE:           float = float(_cbam.get("surcharge_rate", 100_000))

# ── Regulatory Ratchet ──────────────────────────────────────────
_reg = _engine.get("regulatory_ratchet", {})
REG_RATCHET_BASELINE:          float = float(_reg.get("baseline", 10.0))
REG_RATCHET_ROUND_INCREMENT:   float = float(_reg.get("round_increment", 5.0))
REG_RATCHET_FINE_PER_POINT:    float = float(_reg.get("fine_per_point", 500_000))

# ── Supplier Defection ──────────────────────────────────────────
_supplier = _engine.get("supplier_defection", {})
SUPPLIER_DEFECTION_INV_THRESHOLD: float = float(_supplier.get("inv_threshold", 0.15))
SUPPLIER_DEFECTION_OPEX_MULT:  float = float(_supplier.get("opex_multiplier", 1.10))
SUPPLIER_DEFECTION_REV_MULT:   float = float(_supplier.get("rev_multiplier", 0.95))

# ── CFO Austerity ───────────────────────────────────────────────
_cfo = _engine.get("cfo_austerity", {})
CFO_AUSTERITY_LOAN_RATIO:     float = float(_cfo.get("loan_ratio_trigger", 0.5))

# ── Cash Conversion Engine ──────────────────────────────────────
_cash_conv = _engine.get("cash_conversion", {})
CASH_CONVERSION_GOV_DIVISOR:   float = float(_cash_conv.get("gov_risk_divisor", 500.0))
CASH_CONVERSION_EFFICIENCY_FLOOR: float = float(_cash_conv.get("efficiency_floor", 0.5))

# ── DSO / Working Capital ───────────────────────────────────────
_dso = _engine.get("dso", {})
DSO_BASELINE_FACTOR:           float = float(_dso.get("baseline_factor", 0.02))
DSO_GOV_RISK_SCALING:          float = float(_dso.get("gov_risk_scaling", 0.001))
DSO_MAX_CAP:                   float = float(_dso.get("max_cap", 0.15))

# ── Macro Noise ─────────────────────────────────────────────────
_noise = _engine.get("macro_noise", {})
MACRO_NOISE_INFLATION_BAND:    float = float(_noise.get("inflation_band", 0.004))
MACRO_NOISE_CARBON_BAND:       float = float(_noise.get("carbon_price_band", 0.07))
MICRO_STRIKE_PROBABILITY:     float = float(_noise.get("micro_strike_probability", 0.06))
MICRO_STRIKE_OPEX_RATE:        float = float(_noise.get("micro_strike_opex_rate", 0.05))

# ── FX Risk ─────────────────────────────────────────────────────
_fx = _engine.get("fx_risk", {})
FX_MOVEMENT_BAND:              float = float(_fx.get("movement_band", 0.07))
FX_DEFAULT_EXPOSURE:           float = float(_fx.get("default_exposure", 0.20))

# ── Emissions Breach ────────────────────────────────────────────
_emissions = _engine.get("emissions_breach", {})
EMISSIONS_BREACH_REP_PENALTY:  float = float(_emissions.get("rep_penalty", 5.0))

# ── Stranded Assets ─────────────────────────────────────────────
_stranded = _engine.get("stranded_assets", {})
STRANDED_ASSET_CI_THRESHOLD:   int   = int(_stranded.get("ci_threshold", 120))
STRANDED_ASSET_COC_SURCHARGE:  float = float(_stranded.get("coc_surcharge", 0.015))

# ── Tipping Point Hostility Multipliers ─────────────────────────
_tip_host = _engine.get("tipping_hostility", {})
TIPPING_HOSTILITY_TIPPED:     float = float(_tip_host.get("tipped_multiplier", 2.5))
TIPPING_HOSTILITY_STRESSED:   float = float(_tip_host.get("stressed_multiplier", 1.75))
TIPPING_HOSTILITY_WARNING:    float = float(_tip_host.get("warning_multiplier", 1.25))

# ── NCD Forgiveness ─────────────────────────────────────────────
_forgive = _engine.get("ncd_forgiveness", {})
NCD_FORGIVENESS_LOG_COEFF:     float = float(_forgive.get("log_coefficient", 2.0))

# ── Implementation Lag ──────────────────────────────────────────
_impl_lag = _engine.get("implementation_lag", {})
IMPLEMENTATION_LAG_INV_THRESHOLD: float = float(_impl_lag.get("inv_threshold", 0.10))

# ── Employer Brand ──────────────────────────────────────────────
_eb = _engine.get("employer_brand", {})
EMPLOYER_BRAND_PENALTY_THRESHOLD: int = int(_eb.get("penalty_threshold", 40))
EMPLOYER_BRAND_MAX_PENALTY_RATE: float = float(_eb.get("max_penalty_rate", 0.08))

# ── Patient Outcomes (Healthcare BUs) ───────────────────────────
_po = _engine.get("patient_outcomes", {})
PATIENT_OUTCOMES_BASELINE:     float = float(_po.get("baseline", 50.0))
PATIENT_OUTCOMES_DIVISOR:      float = float(_po.get("divisor", 200.0))
PATIENT_OUTCOMES_MOD_MIN:      float = float(_po.get("modifier_min", 0.75))
PATIENT_OUTCOMES_MOD_MAX:      float = float(_po.get("modifier_max", 1.25))

# ── Utilization (Healthcare BUs) ────────────────────────────────
_util = _engine.get("utilization", {})
UTILIZATION_OVERLOAD_THRESHOLD: float = float(_util.get("overload_threshold", 85.0))
UTILIZATION_OVERLOAD_BURNOUT_INC: float = float(_util.get("overload_burnout_increment", 10.0))
UTILIZATION_DRIFT_RATE:        float = float(_util.get("drift_rate", 0.10))

# ── Imitation Decay ─────────────────────────────────────────────
_imit = _engine.get("imitation_decay", {})
DEFAULT_IMITATION_DECAY_RATE:  float = float(_imit.get("default_rate", 0.10))

# ── Scoring / Grading Boundaries ────────────────────────────────
_scoring = _engine.get("scoring", {})
SEVERITY_ROUTINE_CEILING:      int   = int(_scoring.get("severity_routine_ceiling", 1))
SEVERITY_NOTEWORTHY_CEILING:   int   = int(_scoring.get("severity_noteworthy_ceiling", 5))
SEVERITY_MATERIAL_CEILING:     int   = int(_scoring.get("severity_material_ceiling", 15))
SDG_GRADE_A_PLUS:              int   = int(_scoring.get("sdg_grade_a_plus", 80))
SDG_GRADE_A:                   int   = int(_scoring.get("sdg_grade_a", 70))
SDG_GRADE_B:                   int   = int(_scoring.get("sdg_grade_b", 55))
SDG_GRADE_C:                   int   = int(_scoring.get("sdg_grade_c", 40))
SDG_GRADE_D:                   int   = int(_scoring.get("sdg_grade_d", 25))
CAROIC_GRADE_A_PLUS:           int   = int(_scoring.get("caroic_grade_a_plus", 25))
CAROIC_GRADE_A:                int   = int(_scoring.get("caroic_grade_a", 15))
CAROIC_GRADE_B:                int   = int(_scoring.get("caroic_grade_b", 10))
CAROIC_GRADE_C:                int   = int(_scoring.get("caroic_grade_c", 5))
CRI_WEIGHT_GOV_RISK:           float = float(_scoring.get("cri_weight_gov_risk", 0.3))
CRI_WEIGHT_SLO_DEFICIT:        float = float(_scoring.get("cri_weight_slo_deficit", 0.3))
CRI_WEIGHT_REP_DEFICIT:        float = float(_scoring.get("cri_weight_rep_deficit", 0.2))
CRI_WEIGHT_CARBON:             float = float(_scoring.get("cri_weight_carbon", 0.2))
CRI_TIER_LOW:                  int   = int(_scoring.get("cri_tier_low", 25))
CRI_TIER_MODERATE:             int   = int(_scoring.get("cri_tier_moderate", 50))
CRI_TIER_HIGH:                 int   = int(_scoring.get("cri_tier_high", 75))
MOMENTUM_WEIGHT_TREASURY:      float = float(_scoring.get("momentum_weight_treasury", 0.4))
MOMENTUM_WEIGHT_REP:           float = float(_scoring.get("momentum_weight_rep", 0.3))
MOMENTUM_WEIGHT_NCD:           float = float(_scoring.get("momentum_weight_ncd", 0.3))
MOMENTUM_HIGH_THRESHOLD:       int   = int(_scoring.get("momentum_high_threshold", 70))
MOMENTUM_COMEBACK_MR_BONUS:    float = float(_scoring.get("momentum_comeback_mr_bonus", 0.05))
MOMENTUM_TREASURY_NORM:        int   = int(_scoring.get("momentum_treasury_norm", 500))
MOMENTUM_REP_MULTIPLIER:       int   = int(_scoring.get("momentum_rep_multiplier", 5))
MOMENTUM_NCD_MULTIPLIER:       int   = int(_scoring.get("momentum_ncd_multiplier", 10))
INSOLVENCY_WARNING_ROUNDS:     int   = int(_scoring.get("insolvency_warning_rounds", 3))
TIME_TO_IMPACT_HORIZON:        int   = int(_scoring.get("time_to_impact_horizon", 5))
BRAINDRAIN_REP_THRESHOLD:      int   = int(_scoring.get("braindrain_rep_threshold", 25))
STRIKE_WARNING_THRESHOLD:      float = float(_scoring.get("strike_warning_threshold", 0.20))
STRIKE_CRITICAL_THRESHOLD:     float = float(_scoring.get("strike_critical_threshold", 0.40))
CONTAGION_RISK_WARNING:        int   = int(_scoring.get("contagion_risk_warning_threshold", 60))
TREASURY_DROP_REFLECTION_PCT:  int   = int(_scoring.get("treasury_drop_reflection_pct", 20))


# ═════════════════════════════════════════════════════════════════
#  LAYER 2 — CLIMATE VaR PARAMETERS
# ═════════════════════════════════════════════════════════════════

_climate_var = SIMULATION_CONFIG.get("climate_var_parameters", {})

CYCLONE_PROB_BASE:             float = float(_climate_var.get("cyclone_prob_base", 0.75))
CYCLONE_PROB_TIPPED:           float = float(_climate_var.get("cyclone_prob_tipped", 0.90))
CYCLONE_PROB_STRESSED:         float = float(_climate_var.get("cyclone_prob_stressed", 0.85))
CYCLONE_PROB_WARNING:          float = float(_climate_var.get("cyclone_prob_warning", 0.80))
PHYSICAL_VAR_DAMAGE_BASE:      float = float(_climate_var.get("physical_damage_base", 12_000_000))
TIPPING_CI_WARNING:            int   = int(_climate_var.get("tipping_ci_warning", 45))
TIPPING_CI_STRESSED:           int   = int(_climate_var.get("tipping_ci_stressed", 55))
TIPPING_CI_TIPPED:             int   = int(_climate_var.get("tipping_ci_tipped", 65))
TRANSITION_VAR_CI_THRESHOLD:   int   = int(_climate_var.get("transition_var_ci_threshold", 80))
TRANSITION_VAR_STRANDED_MULT:  float = float(_climate_var.get("transition_var_stranded_multiplier", 0.15))
TRANSITION_VAR_FEE_YEARS:      int   = int(_climate_var.get("transition_var_fee_years", 5))


# ═════════════════════════════════════════════════════════════════
#  LAYER 2 — BALANCE SHEET ACCOUNTING
# ═════════════════════════════════════════════════════════════════

_bs_acct = SIMULATION_CONFIG.get("balance_sheet_accounting", {})

BS_CAPEX_CAPITALISATION_RATE:  float = float(_bs_acct.get("capex_capitalisation_rate", 0.60))
BS_ANNUAL_DEPRECIATION_RATE:   float = float(_bs_acct.get("annual_depreciation_rate", 0.10))
BS_BRAND_BASE_PER_BU:         float = float(_bs_acct.get("brand_base_per_bu", 6_250_000))
BS_MIN_ENVIRONMENTAL_PROVISION: float = float(_bs_acct.get("min_environmental_provision", 1_000_000))
BS_DECOMMISSIONING_ACCRETION:  float = float(_bs_acct.get("decommissioning_accretion_rate", 0.03))


# ═════════════════════════════════════════════════════════════════
#  LAYER 2 — TERMINAL VALUATION
# ═════════════════════════════════════════════════════════════════

_tv = SIMULATION_CONFIG.get("terminal_valuation", {})

TV_SHARES_OUTSTANDING:         int   = int(_tv.get("shares_outstanding", 100_000_000))
TV_IPO_PRICE:                  float = float(_tv.get("ipo_price_per_share", 50.0))
TV_LONG_RUN_GROWTH:            float = float(_tv.get("long_run_growth", 0.02))
TV_EXIT_MULTIPLE_FLOOR:        float = float(_tv.get("exit_multiple_floor", 6.0))
TV_EXIT_MULTIPLE_CEILING:      float = float(_tv.get("exit_multiple_ceiling", 18.0))

# GAME-3: Cross-pathway leaderboard difficulty coefficients (config-driven).
# These normalise raw M_R across the 5 ending pathways so teams on harder
# pathways are not unfairly ranked. Regenerate empirically with
# scripts/calibrate_pathway_difficulty.py (writes back into this JSON key);
# the hard-coded fallback below preserves the previous hand-set values.
TV_PATHWAY_DIFFICULTY: dict = dict(_tv.get("pathway_difficulty", {
    "activist_ultimatum": 1.00,
    "climate_black_swan": 1.15,
    "stakeholder_revolt": 1.10,
    "hostile_takeover":   1.20,
    "regulatory_shutdown": 1.12,
}))


# ═════════════════════════════════════════════════════════════════
#  LAYER 2 — BLACK SWAN LIMITS
# ═════════════════════════════════════════════════════════════════

_bsl = SIMULATION_CONFIG.get("black_swan_limits", {})

BLACK_SWAN_MAX_EVENT_PROBABILITY: float = float(_bsl.get("max_event_probability", 0.12))


# ═════════════════════════════════════════════════════════════════
#  LAYER 2 — TURNAROUND PATHWAY (numeric parameters only)
#  Narrative strings remain in engine.py as code-level constants.
# ═════════════════════════════════════════════════════════════════

_ta = SIMULATION_CONFIG.get("turnaround_pathway", {})
_ta_crisis = _ta.get("crisis", {})
_ta_stab   = _ta.get("stabilisation", {})
_ta_rec    = _ta.get("recovery", {})
_ta_exit   = _ta.get("exit", {})

TURNAROUND_CRISIS_ENTRY_TREASURY: float = float(_ta_crisis.get("entry_treasury", 0))
TURNAROUND_CRISIS_ENTRY_REP:      float = float(_ta_crisis.get("entry_reputation", 30))
TURNAROUND_CRISIS_BAILOUT:        float = float(_ta_crisis.get("bailout", 3_000_000))
TURNAROUND_CRISIS_CAPEX_CAP:      float = float(_ta_crisis.get("capex_cap", 0.0))
TURNAROUND_CRISIS_MR_CAP:         float = float(_ta_crisis.get("mr_cap", 0.60))

TURNAROUND_STAB_EXIT_TREASURY:    float = float(_ta_stab.get("exit_treasury", 0))
TURNAROUND_STAB_EXIT_REP:         float = float(_ta_stab.get("exit_reputation", 20))
TURNAROUND_STAB_CAPEX_CAP:        float = float(_ta_stab.get("capex_cap", 0.50))
TURNAROUND_STAB_MR_CAP:           float = float(_ta_stab.get("mr_cap", 0.80))

TURNAROUND_RECOVERY_EXIT_TREASURY: float = float(_ta_rec.get("exit_treasury", 10_000_000))
TURNAROUND_RECOVERY_EXIT_REP:     float = float(_ta_rec.get("exit_reputation", 45))
TURNAROUND_RECOVERY_CAPEX_CAP:    float = float(_ta_rec.get("capex_cap", 1.0))
TURNAROUND_RECOVERY_MR_CAP:       float = float(_ta_rec.get("mr_cap", 1.20))

TURNAROUND_EXIT_TREASURY:         float = float(_ta_exit.get("exit_treasury", 20_000_000))
TURNAROUND_EXIT_REP:              float = float(_ta_exit.get("exit_reputation", 55))
TURNAROUND_EXIT_MR_BONUS:         float = float(_ta_exit.get("mr_bonus", 0.10))


# ═════════════════════════════════════════════════════════════════
#  HOT-RELOAD SUPPORT
#  Called by admin config upload endpoint after writing new JSON.
# ═════════════════════════════════════════════════════════════════

def reload_simulation_config() -> dict:
    """Re-read simulation_config.json and update ALL module-level constants.

    Uses importlib.reload on this module, which re-executes all top-level
    code — re-reads JSON, re-computes all typed constants from the fresh
    SIMULATION_CONFIG dict.

    Returns the updated SIMULATION_CONFIG dict.
    """
    import importlib
    importlib.reload(sys.modules[__name__])
    # After reload, the module's globals are refreshed.
    # Return the new SIMULATION_CONFIG from the reloaded module.
    return sys.modules[__name__].SIMULATION_CONFIG
