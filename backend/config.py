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

# ── Decision paradigms ──────────────────────────────────────────────────────
# THE authoritative set. router.create_session validates against it and the
# bulk-upload Excel template builds its dropdown from it, so the two can never
# disagree. (2026-07-20: they already had — the bulk-upload help text offered
# `un_sdg`, which create_session rejects with 422, so a "valid" import could
# produce a facilitator whose default paradigm could not create a cohort.)
# Adding a paradigm here is NOT sufficient on its own: the engine must handle
# it end to end before it is offered to facilitators.
# 2026-09-03: brsr_ngrbc added. It was in the Pydantic enum (models.py) and had
# a full engine path (round_logic.post_tick's brsr branch, brsr_controller, the
# side-track module) but was NOT in this set, so create_session answered 422 and
# no cohort could ever reach it — the same shape as the un_sdg defect above,
# with the opposite sign. Added only now that _post_brsr_grand_finale computes
# M_R through terminal_valuation.calculate_mr like every other finale; before
# that it scored on hard steps where the canon ramps.
VALID_DECISION_PARADIGMS: frozenset[str] = frozenset({
    "legacy_abc", "multi_toggles", "advanced_climate", "healthcare", "brsr_ngrbc",
})

# Connection pool settings
#
# PERF-AUDIT-2026-07-29: the max was 10, which DEADLOCKED a normal class.
# A commit holds one connection for its advisory lock for the whole commit
# while its own queries take further connections from the same pool, so each
# in-flight commit costs ~2. Measured on real Postgres: 12 students committing
# simultaneously against a pool of 10 never returned (pool.acquire had no
# timeout, so requests waited on each other indefinitely); the same 12 against
# a pool of 40 completed in 0.4s, and 20 students in 0.5s.
#
# The floor therefore has to clear 2 x the 20-player roster ceiling with
# headroom for facilitator dashboards and websockets. 40 does that and still
# sits well inside a managed Postgres default of ~100 — but note the pool is
# PER WORKER, so if you ever raise WEB_CONCURRENCY, keep
# workers x DB_MAX_CONNECTIONS under the server's max_connections.
DB_MIN_CONNECTIONS: int = int(os.getenv("DB_MIN_CONNECTIONS", "2"))
DB_MAX_CONNECTIONS: int = int(os.getenv("DB_MAX_CONNECTIONS", "40"))

# Never wait forever for a connection: an exhausted pool must surface as a
# visible 503 the facilitator can act on, not a class-wide hang.
DB_ACQUIRE_TIMEOUT_SECONDS: float = float(os.getenv("DB_ACQUIRE_TIMEOUT_SECONDS", "10"))
DB_COMMAND_TIMEOUT_SECONDS: float = float(os.getenv("DB_COMMAND_TIMEOUT_SECONDS", "30"))

# F-26 (launch audit 2026-09-01): a commit holds ONE pooled connection for its
# advisory lock for the whole tick while its own queries take a SECOND one from
# the same pool. Once DB_MAX_CONNECTIONS commits are in flight at once every
# one of them is waiting for a connection none of them will release — measured
# on real Postgres: 40 simultaneous R1 commits → 0 succeed, 39 time out after
# DB_ACQUIRE_TIMEOUT_SECONDS and 1 gets a 503. Thirty cohorts sharing a round
# deadline is exactly that shape. The gate bounds in-flight commits per worker
# so each can always obtain its second connection, and leaves a couple spare
# for dashboard polls. Excess commits QUEUE (the gate is fair, in arrival
# order) and only fail — with a 503 the cockpit retries — if they wait longer
# than COMMIT_QUEUE_TIMEOUT_SECONDS.
COMMIT_MAX_IN_FLIGHT: int = max(1, int(os.getenv(
    "COMMIT_MAX_IN_FLIGHT", str(max(1, DB_MAX_CONNECTIONS // 2 - 1)))))
COMMIT_QUEUE_TIMEOUT_SECONDS: float = float(os.getenv("COMMIT_QUEUE_TIMEOUT_SECONDS", "45"))

# F-40 follow-up (2026-09-02): random player ids are `MUR-` + N upper-case
# letters, unique across the whole platform for its lifetime (ids are never
# reissued, deleted cohorts included). Three letters gave 17,576 ids — about a
# hundred 150-team launches before the allocator would start to struggle; four
# give 456,976. Older three-letter ids stay valid: nothing validates the width,
# the uniqueness check covers both. Floor 3, cap 8.
PLAYER_ID_RANDOM_LETTERS: int = max(3, min(8, int(os.getenv("PLAYER_ID_RANDOM_LETTERS", "4"))))

# App settings
APP_TITLE: str = "Muressons Global Corporation API"
APP_VERSION: str = "1.0.0"
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# God-Mode Master Password — admin break-glass. Logs into god_mode and bypasses
# any FACILITATOR login. P6: it NO LONGER unlocks player accounts — player
# master-unlock uses the separate PLAYER_MASTER_PASSWORD below, so a leak of this
# admin secret cannot span into the player realm.
# QA-2026-07-16 #1: NO committed default. Empty => the bypass is DISABLED
# (verify_master_password() returns False on an empty secret). Arm it by
# setting MASTER_PASSWORD in the environment (backend/.env locally, Railway
# Variables in prod): openssl rand -base64 24. The old committed fallback is in
# git history -- treat it as burned and never reuse it.
_mp = os.getenv("MASTER_PASSWORD", "").strip().strip('"').strip("'")
MASTER_PASSWORD: str = _mp

# P6: Player master-unlock secret — SEPARATE from the admin MASTER_PASSWORD so a
# leak of one break-glass credential cannot span both the admin and player
# realms. When set, it lets support staff log into any player account. DISABLED
# by default (empty); set PLAYER_MASTER_PASSWORD to a value DISTINCT from
# MASTER_PASSWORD to enable. It intentionally does NOT fall back to
# MASTER_PASSWORD — separation is the whole point.
_plmp = os.getenv("PLAYER_MASTER_PASSWORD", "").strip().strip('"').strip("'")
PLAYER_MASTER_PASSWORD: str = _plmp

# Project-Admin password — logs into the virtual 'project_admin' account.
# That role can ONLY create facilitators (incl. Excel bulk upload) and
# cohorts; it can never run or manage a simulation.
# Override via PROJECT_ADMIN_PASSWORD env var; set "" to keep the default.
# QA-2026-07-16 #1: NO committed default. Empty => project_admin login is
# DISABLED (the login compare requires a non-empty secret). Arm via the
# PROJECT_ADMIN_PASSWORD env var. The old committed fallback is in git history.
_pap = os.getenv("PROJECT_ADMIN_PASSWORD", "").strip().strip('"').strip("'")
PROJECT_ADMIN_PASSWORD: str = _pap

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

# 3.1 (2026-08-03): resolve through the durable data dir. Previously this was
# the copy inside the IMAGE, so every Excel import / god-mode save survived
# until the next redeploy and then silently reverted, while the upload endpoint
# still reported {"reload": "complete"}. config_file() seeds from the committed
# copy when the volume is empty, so behaviour is unchanged wherever no volume
# is configured (local dev, CI) — see runtime_paths.config_file.
from runtime_paths import config_file as _config_file  # noqa: E402
CONFIG_PATH = _config_file("simulation_config.json")
# CFG-10 (2026-09-06): a volume seeded by an intermediate build carries that
# build's transient values forever; known superseded values are rewritten to
# the current ones BEFORE the file is read — see config_migrations.py. Recorded
# here for /health (`config.migrated`) and reset on reload like every other
# module-level value.
from config_migrations import apply_known_migrations as _apply_known_migrations  # noqa: E402
CONFIG_MIGRATIONS: list[dict] = _apply_known_migrations(CONFIG_PATH)
SIMULATION_CONFIG = {}
if CONFIG_PATH.exists():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            SIMULATION_CONFIG = json.load(f)
    except Exception as e:
        print(f"[CONFIG] Warning: Failed to load simulation_config.json: {e}")

# CFG-02/03 (audit 2026-09-04, WP-20): every sanity clamp below used to be a
# bare print() — a stdout line nobody reads on Railway, invisible to /health,
# to /api/admin/config/live and to the facilitator. The ledger records each
# clamp so those surfaces can report "the volume config carries a legacy value
# and the engine is NOT running what the file says". Reset on reload, like
# every other module-level value here.
CONFIG_CLAMPS: list[dict] = []


def _clamp(key: str, configured, using, reason: str) -> None:
    """Record and announce a sanity clamp: `key` on the data volume said
    `configured`; the engine runs `using`."""
    CONFIG_CLAMPS.append({"key": key, "configured": configured, "using": using, "reason": reason})
    print(f"[CONFIG] WARNING: {key}={configured} {reason}; using {using}. "
          "Update simulation_config.json on the data volume.")


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

# Corporate Sustainability Fund investable pool = max(treasury * fraction, floor).
# Mirrors the player cockpit csfPool (router.py commit-turn ratio recompute).
CSF_POOL_TREASURY_FRACTION:         float = float(_financial.get("csf_pool_treasury_fraction", 0.20))
CSF_POOL_FLOOR:                     float = float(_financial.get("csf_pool_floor", 5_000_000))

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

# F-10 (launch audit 2026-09-01): NCD is an INDEX (seed 0; the docs' working
# range is 30–200; ten rounds of outright neglect reach ≈2,170). The previous
# values were dollar-scale (1,000,000 / 500,000 / 50,000) and could never be
# reached, so the credit-downgrade card, the forecast countdown and the
# Advanced-Climate NCD OPEX penalty (NCD 1000 → $250) were permanently inert.
# Absolute hard cap on Natural Capital Debt per BU (VULN-007) — index units.
NCD_HARD_CAP:              float = float(_ncd.get("hard_cap", 5_000))

# Warning threshold — triggers the credit-downgrade narrative (index units;
# a neglect trajectory crosses it around round 5).
NCD_WARN_THRESHOLD:        float = float(_ncd.get("warn_threshold", 1_000))

# $ of OPEX penalty per NCD index unit (× hostility multiplier), Advanced
# Climate paradigm. NCD 1,000 → $1M per round on a ~$20M BU; the penalty is
# still capped at 50% (75% when tipped) of the BU's revenue.
NCD_OPEX_PENALTY_PER_UNIT: float = float(_ncd.get("opex_penalty_per_unit", 1_000))

# Deployed volumes keep their own simulation_config.json (runtime_paths.
# config_file), so a volume that still carries the dollar-scale values would
# keep the mechanics inert forever. Anything above 100,000 is unambiguously
# the legacy scale: fall back to the index defaults and say so.
if NCD_HARD_CAP > 100_000 or NCD_WARN_THRESHOLD > 100_000:
    _clamp("ncd_parameters.hard_cap/warn_threshold", f"{NCD_HARD_CAP:,.0f}/{NCD_WARN_THRESHOLD:,.0f}",
           "5,000/1,000", "are dollar-scale legacy values (F-10)")
    NCD_HARD_CAP, NCD_WARN_THRESHOLD = 5_000.0, 1_000.0
if "opex_penalty_per_unit" not in _ncd and "opex_scaling_factor" in _ncd:
    _clamp("ncd_parameters.opex_scaling_factor", _ncd.get("opex_scaling_factor"),
           "opex_penalty_per_unit=1,000", "is the legacy key (F-10)")

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
# F-06 (launch audit 2026-09-01): the synergy efficiency used to be applied as
# `opex × (1 − √ratio × 0.7 × synergy)` EVERY round — −35% per round at a 25%
# ratio, compounding to the 35% floor by R4–R5, so a modest investment removed
# two-thirds of costs in four rounds. The curve is now a fraction of a hard
# per-round ceiling: reduction = ceiling × min(1, √ratio × dampening × synergy).
# At the default 6%: a 25%-ratio team saves ≈2.1%/round (≈−19% over ten
# rounds), an all-in team ≈4.2%/round (≈−35%); the first-seen-OPEX floor
# (engine.SYNERGY_OPEX_FLOOR_FRACTION) still applies.
SYNERGY_MAX_REDUCTION_PER_ROUND: float = float(_synergy.get("max_reduction_per_round", 0.06))

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
# FIN-10 (audit 2026-09-04): the uncapped multiplier reached ×2.975 per round
# (rep 0 + burnout 100) on hospitals/clinics/software — attrition-driven cost
# inflation in hospital systems runs 5–15% (agency/locum premiums). Calibration
# call: cap the retention premium at +30% of OPEX per round.
BRAINDRAIN_PENALTY_CAP:         float = float(_braindrain.get("penalty_cap", 1.30))

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
# RECOVERED (workspace file-sync loss): a coalition formed last round raises this
# round's strike risk via _coalition_mult = 1 + coalition_pressure * gain (engine.py).
# Default 0.5 reconstructed (a full coalition => 1.5x strike probability); verify vs source.
COALITION_STRIKE_GAIN:          float = float(_strike.get("coalition_strike_gain", 0.5))

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

# ── Stakeholder realism waves — tunables (SPEC F1–F5) ────────────
# All config-Excel backed. Consumed by the stakeholder memory/reactive waves in
# npc_stakeholders.py, systemic_risk_engine.py, stakeholder_engagement.py and
# autonomous_agents.py. Only active when the matching per-cohort toggle is on.
# F1 — trust stock & betrayal scar
_trust = _engine.get("stakeholder_trust", {})
TRUST_GAIN_RATE:      float = float(_trust.get("gain_rate", 0.25))
TRUST_LOSS_RATE:      float = float(_trust.get("loss_rate", 0.55))
TRUST_SCAR_IMMEDIATE: float = float(_trust.get("scar_immediate", 12.0))
TRUST_SCAR_DURATION:  int   = int(_trust.get("scar_duration", 3))
TRUST_SCAR_CEILING:   float = float(_trust.get("scar_ceiling", 60.0))
NPC_SENTIMENT_BRIDGE_WEIGHT: float = float(_trust.get("sentiment_bridge_weight", 0.30))
# F2 — continuous SLO feedback
STAKEHOLDER_SLO_COUPLING: float = float(_engine.get("stakeholder_slo_feedback", {}).get("coupling", 1.0))
# F5 — engagement actions & promise ledger
_engage = _engine.get("stakeholder_engagement", {})
ENGAGE_TOWNHALL_COST:    float = float(_engage.get("townhall_cost", 500_000))
ENGAGE_TOWNHALL_TRUST:   float = float(_engage.get("townhall_trust", 3.0))
ENGAGE_PLEDGE_COST:      float = float(_engage.get("pledge_cost", 1_000_000))
ENGAGE_PLEDGE_TRUST:     float = float(_engage.get("pledge_trust", 6.0))
ENGAGE_COMMIT_COST:      float = float(_engage.get("commit_cost", 300_000))
ENGAGE_COMMIT_TRUST:     float = float(_engage.get("commit_trust", 4.0))
PROMISE_DEFAULT_HORIZON:  int  = int(_engage.get("default_horizon", 3))
PROMISE_KEPT_TRUST_BONUS: float = float(_engage.get("kept_trust_bonus", 8.0))
PROMISE_KEPT_SLO_CREDIT:  float = float(_engage.get("kept_slo_credit", 4.0))
PROMISE_KEPT_REP_CREDIT:  float = float(_engage.get("kept_rep_credit", 3.0))
PROMISE_BROKEN_REP_DING:  float = float(_engage.get("broken_rep_ding", 6.0))
# F3 — coalitions & salience contagion
_coal = _engine.get("stakeholder_coalitions", {})
COALITION_TIER_MIN:    int   = int(_coal.get("tier_min_index", 2))
COALITION_F2_GAIN:     float = float(_coal.get("f2_gain", 0.5))
COALITION_STRIKE_GAIN: float = float(_coal.get("strike_gain", 0.5))
CONTAGION_SAT_NUDGE:   float = float(_coal.get("contagion_nudge", 5.0))
# F4 — threshold uncertainty & patience
_uncert = _engine.get("stakeholder_uncertainty", {})
THRESHOLD_JITTER: float = float(_uncert.get("jitter", 4.0))
PATIENCE_LIMIT:   int   = int(_uncert.get("patience_limit", 3))

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
# F-03 (launch audit 2026-09-01): a PRICE PER TONNE of CO2e. The shipped value
# was 100_000, which turned the R3/R7 Scope-1+2 levy into an $80–110M hit on a
# $50M treasury (EU CBAM certificates trade around €75/t). Because the live
# config is read from the durable data dir, a stale volume copy could carry the
# old number forever, so anything above _CBAM_SURCHARGE_SANITY_MAX is treated as
# the legacy per-kilotonne mistake and clamped to the default with a warning.
_CBAM_SURCHARGE_DEFAULT: float = 100.0
_CBAM_SURCHARGE_SANITY_MAX: float = 5_000.0
CBAM_SURCHARGE_RATE:           float = float(_cbam.get("surcharge_rate", _CBAM_SURCHARGE_DEFAULT))
if CBAM_SURCHARGE_RATE > _CBAM_SURCHARGE_SANITY_MAX:
    _clamp("engine_parameters.cbam.surcharge_rate", CBAM_SURCHARGE_RATE, _CBAM_SURCHARGE_DEFAULT,
           f"$/tCO2e exceeds the {_CBAM_SURCHARGE_SANITY_MAX:,.0f} sanity ceiling (legacy value)")
    CBAM_SURCHARGE_RATE = _CBAM_SURCHARGE_DEFAULT

# ── Regulatory Ratchet ──────────────────────────────────────────
_reg = _engine.get("regulatory_ratchet", {})
# F-10: baseline 10 → 20. The seed mean governance risk is 17.5, so at 10 every
# team paid an unavoidable $3.75M fine in round 1 and $1.25M in round 2 before
# any decision had taken effect. At 20 the seed is compliant; the fine bites
# when governance actually deteriorates.
_REG_RATCHET_BASELINE_DEFAULT: float = 20.0
# Audit 2026-09-04 F-07: this was the ONE stale-volume value with no clamp.
# A data volume seeded before F-10 (2026-09-01) still says 10.0; CBAM, the
# NCD thresholds and the imitation rate are clamped with a warning, this key
# governed silently — every team lost $1.6M (generic seed) to $3.75M
# (healthcare seed) in round 1 before any decision, with an R1 event card
# blaming "persistent non-compliance". Anything at or below the pre-F-10
# value is treated as the legacy mistake and clamped to the default; the
# tuning band ABOVE it (a stricter regulator) is honoured as configured.
_REG_RATCHET_BASELINE_LEGACY_MAX: float = 10.0
REG_RATCHET_BASELINE:          float = float(_reg.get("baseline", _REG_RATCHET_BASELINE_DEFAULT))
if REG_RATCHET_BASELINE <= _REG_RATCHET_BASELINE_LEGACY_MAX:
    _clamp("engine_parameters.regulatory_ratchet.baseline", REG_RATCHET_BASELINE, _REG_RATCHET_BASELINE_DEFAULT,
           f"is at or below the pre-F-10 value {_REG_RATCHET_BASELINE_LEGACY_MAX} (seed teams are fined in round 1)")
    REG_RATCHET_BASELINE = _REG_RATCHET_BASELINE_DEFAULT
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
# Calibration ruling B (2026-09-01, CALIBRATION_DIAGNOSIS): revenue gains
# inflation pass-through at this fraction of cost inflation, so inflation is
# margin pressure (costs outrun prices by 1-q) instead of a one-sided death
# tax on a revenue base that never grew. 0.0 restores the old behaviour.
# EVAL_Stakeholder_SLO recs 4+5 (2026-09-01): absolute-capex escapes so the
# post-repair richer economy doesn't silently harden relative thresholds, a
# mild middle growth tier for SLO, and a baseline sentiment-bridge weight
# that keeps the heat-map and NPC surfaces aligned even with F1 off.
_slo_ramp = _engine.get("slo_ramp", {})
NATURAL_DECAY_GROWTH_ABS_CAPEX: float = float(_slo_ramp.get("growth_abs_capex", 3_000_000))
NATURAL_DECAY_MID_GROWTH:       float = float(_slo_ramp.get("mid_growth", 1.0))

# ── Natural-decay tier calibration (launch readiness 2026-09-03) ────────────
# THE RATIO BANDS ARE THE ORIGINAL 0.15 / 0.20 / 0.30. They were moved to
# 0.10 / 0.25 / 0.50 and then dialled back to here after measuring, because the
# case for moving them did not survive the measurement:
#
#  * they change NOTHING in the balance report or the treasury fingerprints at
#    any value between 0.30 and 0.50 — the bot ladder runs at investment ratios
#    0.0125-0.15, below every candidate bar, so the runner never sees them;
#  * their only real effect was on teams above ratio 0.30, and moving the growth
#    bar to 0.40 cost the stakeholder golden trace 21.25 SLO points by R10 and
#    escalated a stakeholder to `protest` from R7 — for a fixture sitting at the
#    4th percentile of substantive play;
#  * and reverting the growth bar WITHOUT also reverting the mild bar left the
#    mild tier catching 1.7% of real decisions, NARROWER than the 3.7% it
#    started at. A dial-back that leaves a new degeneracy behind is not a
#    dial-back, so both went back together.
#
# What the original bands genuinely had wrong was not their VALUES. It was that
# the decay tier underneath them was unreachable — see min_abs_capex below.
# That is the one behavioural change that survives, and it is a defect fix
# rather than a calibration judgement.
#
# Measured tier populations over the 241 stored real decisions, floor $100k:
#   0.15 / 0.20 / 0.30  (shipped)  decay 70.1%  no-decay 0.0%  mild 3.7%  growth 26.1%
#   0.10 / 0.25 / 0.40             decay 70.1%  no-decay 2.1%  mild 5.8%  growth 22.0%
#   0.10 / 0.25 / 0.30             decay 70.1%  no-decay 2.1%  mild 1.7%  growth 26.1%
#
# F-17 (audit 2026-09-04, WP-21): until 2026-09-05 engine.py evaluated the tier
# on the GROUP-AVERAGE investment ratio, so the per-decision populations above
# described a quantity the engine never read (a $0 BU grew when the team
# average cleared 0.30). The tier is now the BU's own ratio, as measured here.
# The bands stay 0.15 / 0.20 / 0.30 until the owner's stored-decision export is
# re-measured per BU per tick.
#
# NOTE: no_decay_ratio is structurally INERT given the $100k floor. The CSF pool
# is at least $5M, so any allocation reaching ratio 0.15 is already at least
# $750k and clears the floor on the absolute test first. It is kept as the
# documented band and as the knob to turn if the floor is ever raised.
NATURAL_DECAY_NO_DECAY_RATIO:   float = float(_slo_ramp.get("no_decay_ratio", 0.15))
NATURAL_DECAY_MID_RATIO:        float = float(_slo_ramp.get("mid_ratio", 0.20))
NATURAL_DECAY_GROWTH_RATIO:     float = float(_slo_ramp.get("growth_ratio", 0.30))

# The tier that never fired at all, and why a ratio band alone could not fix it.
# engine.py's call site computed `invested = ratio >= 0.15 or capex_allocated > 0`,
# and router.py refuses any commit giving a BU less than $1 (VULN-009), so
# capex_allocated > 0 held for EVERY decision ever committed. `invested` was
# therefore always True and the full-decay branch was unreachable across the
# whole 0.0-1.0 ratio range, whatever the bands said. A minimum ABSOLUTE spend
# replaces the "> 0" test, mirroring growth_abs_capex at the other end.
#
# $100,000 is chosen from a gap in the real data, not from taste: the 241 stored
# decisions are bimodal — 169 at exactly $1, then NOTHING until $1,000,000, then
# a continuous spread to $9,300,000. Any floor strictly inside ($1, $1,000,000)
# reclassifies exactly the token allocations and cannot misclassify a single
# real one.
#
# DIALLED BACK from $500,000 on 2026-09-03. Every floor from $100k to $999k
# reclassifies the IDENTICAL 169/241 real decisions — the gap makes them
# equivalent in play. They are NOT equivalent in the balance report, because the
# bot ladder allocates $125k-$2.78M per BU, right across the range real teams
# never occupy: at $500k the pure_B reference strategy went bankrupt at R10 and
# the 10% rung's terminal value fell $164M -> $66M; at $100k both are untouched.
# That severity was an artefact of the harness, not a property of the fix, so
# the floor sits at the BOTTOM of the empty interval — same correction for every
# real allocation, least collateral damage to the reference material.
NATURAL_DECAY_MIN_ABS_CAPEX:    float = float(_slo_ramp.get("min_abs_capex", 100_000))

# Bounds. The tiers are only meaningful strictly ordered inside (0, 1], and a
# minimum spend above the growth escape would invert the two absolute tests.
# A configuration that breaks either falls back to the whole default set — never
# to a half-applied mixture — and says so.
_DECAY_TIER_DEFAULTS = (0.15, 0.20, 0.30)
if not (0.0 < NATURAL_DECAY_NO_DECAY_RATIO < NATURAL_DECAY_MID_RATIO
        < NATURAL_DECAY_GROWTH_RATIO <= 1.0):
    _clamp("engine_parameters.slo_ramp.{no_decay,mid,growth}_ratio",
           f"{NATURAL_DECAY_NO_DECAY_RATIO}/{NATURAL_DECAY_MID_RATIO}/{NATURAL_DECAY_GROWTH_RATIO}",
           "/".join(str(x) for x in _DECAY_TIER_DEFAULTS),
           "must satisfy 0 < no_decay_ratio < mid_ratio < growth_ratio <= 1")
    (NATURAL_DECAY_NO_DECAY_RATIO, NATURAL_DECAY_MID_RATIO,
     NATURAL_DECAY_GROWTH_RATIO) = _DECAY_TIER_DEFAULTS
if not (0.0 <= NATURAL_DECAY_MIN_ABS_CAPEX <= NATURAL_DECAY_GROWTH_ABS_CAPEX):
    # CFG-09: the message said "using 500,000" while the code set 100,000.
    _clamp("engine_parameters.slo_ramp.min_abs_capex", f"{NATURAL_DECAY_MIN_ABS_CAPEX:,.0f}", "100,000",
           f"must sit between 0 and growth_abs_capex ({NATURAL_DECAY_GROWTH_ABS_CAPEX:,.0f})")
    NATURAL_DECAY_MIN_ABS_CAPEX = 100_000.0
# C-1 (owner ruling 2026-09-05): the greenwash bar is the TEAM'S share of the
# CSF pool (Σ per-BU ratios) against investment_threshold, and this floor is
# the team's TOTAL CapEx — a group claim is backed by the group's spend. Until
# then both were per-BU averages, so the 15 % bar meant 60 % of the pool for a
# four-BU group and the archetypal real team (one BU at ~50 % of the pool, $1
# in the others) greenwashed on every full claim. engine.greenwash_backing.
GREENWASH_ABS_CAPEX_FLOOR:      float = float(_slo_ramp.get("greenwash_abs_capex_floor", 3_000_000))
NPC_SENTIMENT_BRIDGE_BASELINE:  float = float(_trust.get("sentiment_bridge_baseline", 0.15))

_infl_sym = _engine.get("inflation_symmetry", {})
INFLATION_REVENUE_PASSTHROUGH:  float = float(_infl_sym.get("revenue_passthrough", 0.80))

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
# F-07 (launch audit 2026-09-01): the SERVER applies this rate on every commit
# (the client used to send its own — hard-coded 0.05 while this default said
# 0.10 and the docs said 5%). The config now says what live play has always
# done: 5% per round.
#
# Launch readiness 2026-09-03: F-07 moved the authority from the client to the
# server, which means the value on the DURABLE DATA VOLUME now governs — and a
# volume seeded before F-07 still carries 0.10, exactly double. Nothing failed;
# every team's competitive advantage simply decayed twice as fast (an advantage
# of 0.80 left unattended over a ten-round game reaches 0.5042 at 0.05 and
# 0.3100 at 0.10). Same failure mode, same day, same shape of guard as CBAM
# (~line 471) and the natural-capital thresholds (~line 224): anything above
# the sanity ceiling is treated as the stale pre-F-07 value and clamped to the
# default with a warning naming both. The ceiling deliberately leaves real
# tuning headroom — this key is facilitator-editable through the Excel importer
# (config_excel.py) — while sitting strictly below the known-bad 0.10, so the
# bound can never certify the value it exists to catch.
_IMITATION_DECAY_DEFAULT: float = 0.05
_IMITATION_DECAY_SANITY_MAX: float = 0.08
DEFAULT_IMITATION_DECAY_RATE:  float = float(_imit.get("default_rate", _IMITATION_DECAY_DEFAULT))
if DEFAULT_IMITATION_DECAY_RATE > _IMITATION_DECAY_SANITY_MAX:
    _clamp("engine_parameters.imitation_decay.default_rate", DEFAULT_IMITATION_DECAY_RATE, _IMITATION_DECAY_DEFAULT,
           f"exceeds the {_IMITATION_DECAY_SANITY_MAX:.4g} sanity ceiling (stale pre-F-07 value)")
    DEFAULT_IMITATION_DECAY_RATE = _IMITATION_DECAY_DEFAULT

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

# F-20 (audit 2026-09-04): 100M shares at a $50 IPO implied a $5.0B market cap
# against terminal EVs of $0–0.9B, so every solvent team's reveal priced at
# $1–3 a share ("loss −94%", red). 6.5M shares = baseline EV ($19.2M seed
# EBITDA × 17) ÷ $50, so a $280M EV prices at ≈ $43 and $891M at ≈ $137.
TV_SHARES_OUTSTANDING:         int   = int(_tv.get("shares_outstanding", 6_500_000))
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

# Post-completion Turnaround MODULE (optional, superadmin-gated) — the fixed
# 4-round arc offered after R10 when canonical M_R < threshold. Numeric params
# only; permission state lives in _god_mode_settings (admin_shared.py).
_ta_arc = _ta.get("arc", {})
TURNAROUND_ARC_MAX_ROUNDS:    int   = int(_ta_arc.get("max_rounds", 4))
TURNAROUND_ARC_MR_THRESHOLD:  float = float(_ta_arc.get("eligibility_mr_threshold", 0.80))
TURNAROUND_ARC_ENTRY_BAILOUT: float = float(_ta_arc.get("entry_bailout", 3_000_000))

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
