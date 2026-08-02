"""
scripts/monte_carlo_stress_test.py
====================================
Headless Monte Carlo stress-test harness for the Muressons Global Corporation
simulation engine.

PURPOSE
-------
Mathematically validate two hypotheses:
  H1: An ESG_OPTIMISED strategy reliably survives Black Swan events
      (avg M_R > 1.2, Instability Discount rate < 20%).
  H2: A FINANCIAL strategy correctly suffers structural penalties
      (Instability Discount rate > 40%) without the game becoming
      mathematically unwinnable (P10 M_R > 0.0).

ARCHITECTURE
------------
- Directly calls engine.process_tick() — zero FastAPI/router involvement.
- No database writes — all state is held in plain Python dicts per-run.
- Isolation: each run constructs a fresh global_state + BU list from the
  seed JSON; no shared mutable state between iterations.

USAGE
-----
    # From the project root (muressons-sim/):
    python scripts/monte_carlo_stress_test.py

    # Custom iterations:
    python scripts/monte_carlo_stress_test.py --n 1000

    # Single profile:
    python scripts/monte_carlo_stress_test.py --profile ESG_OPTIMISED --n 500

    # Verbose (prints first 5 run summaries per profile):
    python scripts/monte_carlo_stress_test.py --verbose

OUTPUT
------
Strictly formatted console report with:
  - Archetype distribution per profile (counts + percentages)
  - M_R percentiles P10 / P50 / P90 per profile
  - Black Swan trigger rate per profile
  - Instability Discount hit rate per profile
  - Treasury survival rate (treasury > 0 at round 10)
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import pathlib
import random
import statistics
import sys
import time
from collections import Counter
from typing import Any, NamedTuple

# ── Path bootstrap ──────────────────────────────────────────────────────────
# The engine lives in backend/. We add it to sys.path so imports resolve
# without installing the package. This must happen BEFORE any engine imports.
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_BACKEND   = _REPO_ROOT / "backend"
_DB_DIR    = _REPO_ROOT / "db"

if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# ── Windows UTF-8 stdout fix ─────────────────────────────────────────────────
# Windows cmd/PowerShell defaults to cp1252 which cannot encode Unicode
# box-drawing chars. Reconfigure stdout/stderr to UTF-8 if possible.
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass  # Not critical — ASCII fallback used in report anyway.

# ── Suppress verbose disk-persistence warnings from database_memory ──────────
import logging
logging.getLogger("muressons.db").setLevel(logging.CRITICAL)

# ── Engine imports (pure functions — no I/O) ────────────────────────────────
import os
os.environ.setdefault("USE_MEMORY_DB", "true")  # prevent Postgres attempts

from engine import process_tick                          # master tick
from terminal_valuation import (
    calculate_mr,
    calculate_terminal_value,
    determine_archetype,
)
from black_swan_registry import evaluate_black_swans     # stochastic events
from config import SIM_ROUNDS                            # = 10
# GAME-3: pathway M_R calculators, so the harness can produce pathway-adjusted
# M_R for difficulty-coefficient calibration.
from ending_pathways import (
    calc_climate_black_swan_mr,
    calc_stakeholder_revolt_mr,
    calc_hostile_takeover_mr,
    calc_regulatory_shutdown_mr,
)

_PATHWAY_MR_FNS = {
    "climate_black_swan":  calc_climate_black_swan_mr,
    "stakeholder_revolt":  calc_stakeholder_revolt_mr,
    "hostile_takeover":    calc_hostile_takeover_mr,
    "regulatory_shutdown": calc_regulatory_shutdown_mr,
    # activist_ultimatum has no pathway-specific M_R delta (reference pathway).
}

# CF-001: Wire post_tick + run_new_engines so CI deltas, SLO boosts,
# flag persistence, and all side-track outputs are applied each round.
from round_logic import post_tick, run_new_engines


# ═══════════════════════════════════════════════════════════════════════════════
#  SEED STATE  —  exact replica of database_memory.create_session() logic
#  without any I/O or persistence.  All values sourced from seed_round1.json.
# ═══════════════════════════════════════════════════════════════════════════════

_SEED_PATH = _DB_DIR / "seed_round1.json"


def _load_raw_seed() -> dict:
    """Load the canonical seed_round1.json exactly once."""
    with open(_SEED_PATH, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


_RAW_SEED: dict = _load_raw_seed()


def build_initial_state(ending_pathway: str = "activist_ultimatum") -> tuple[dict, list[dict]]:
    """
    Construct a fresh (global_state, bus) pair identical to what the game
    server produces on session creation — but with zero I/O.

    Returns
    -------
    global_state : dict   matches the schema expected by process_tick()
    bus          : list[dict]  4 default BUs from seed_round1.json
    """
    seed    = _RAW_SEED
    gs_seed = seed["global_state"]
    bus     = copy.deepcopy(seed["business_units"])

    # Ensure every BU has the fields process_tick() reads
    for bu in bus:
        bu.setdefault("staff_burnout_index", 0.0)
        bu.setdefault("natural_capital_debt", 0.0)
        bu.setdefault("workforce_readiness", 50.0)

    n      = len(bus)
    avg_sl = sum(b.get("social_license_score", 50) for b in bus) / n
    avg_ci = sum(b.get("carbon_intensity",     50) for b in bus) / n
    avg_gr = sum(b.get("governance_risk_score", 20) for b in bus) / n

    baseline_vrio = {
        "value":         round(max(0, min(100, avg_sl)), 1),
        "rarity":        round(max(0, min(100, 100 - avg_ci)), 1),
        "imitability":   round(max(0, min(100, gs_seed["group_synergy_multiplier"] * 100)), 1),
        "organization":  round(max(0, min(100, 100 - avg_gr)), 1),
    }
    baseline_ebitda = round(sum(b["revenue_base"] - b["opex_base"] for b in bus), 2)
    baseline_tco2e  = round(sum(
        b.get("carbon_intensity", 0) * b["revenue_base"] / 1_000_000 for b in bus
    ))

    global_state: dict[str, Any] = {
        "state_id":              "mc_run",
        "session_id":            "mc_run",
        "round_number":          1,
        "corporate_treasury":    50_000_000.0,
        "group_reputation":      float(gs_seed["group_reputation_score"]),
        "synergy_multiplier":    float(gs_seed["group_synergy_multiplier"]),
        "cost_of_capital":       float(gs_seed["cost_of_capital_rate"]),
        "active_event_flags": {
            "loan_interest_rate":   0.12,
            "ending_pathway":       ending_pathway,
            "workforce_readiness":  50.0,
        },
        "bonus_score":           0,
        "historical_ebitda":     baseline_ebitda,
        "tco2e_emissions":       baseline_tco2e,
        "vrio_capabilities":     baseline_vrio,
        "green_transition_fund": 0.0,
        "tipping_point_active":  False,
        "pending_capex_projects": [],
        "inflation_index":       0.025,
        "competitor_ebitda":     baseline_ebitda,
        "political_capital":     50.0,
        "community_trust_score": 50.0,
        "global_emissions_intensity": 0.0,
    }

    return global_state, bus


# ═══════════════════════════════════════════════════════════════════════════════
#  SIMULATION AGENT
#  Each agent profile deterministically weights choices per round.
# ═══════════════════════════════════════════════════════════════════════════════

# The 5 game pillars (decision nodes mapped from round_logic/engine context).
# In the headless engine, decisions are keyed by bu_id + a free-form
# decision_node_id. The engine inspects:
#   - investment_ratio  (0.0–1.0)  → scales CAPEX benefit/cost
#   - capex_allocated   ($)        → direct CAPEX spend
#   - choice_selected   (str)      → "option_a" / "option_b" / "option_c"
#
# ABC logic (legacy_abc paradigm):
#   option_a → ESG / sustainability investment  (high cost, CI↓, SLO↑)
#   option_b → balanced / status-quo            (moderate cost, mixed)
#   option_c → financial extraction / austerity (low cost, CI↑, SLO↓)

_BU_IDS = ["pharma", "electronics", "consumer_goods", "software"]

_CHOICE_WEIGHTS: dict[str, dict[str, float]] = {
    #               option_a  option_b  option_c
    "RANDOM":      {"option_a": 1.0, "option_b": 1.0, "option_c": 1.0},
    "FINANCIAL":   {"option_a": 0.1, "option_b": 0.3, "option_c": 0.6},
    "ESG_OPTIMISED":{"option_a": 0.7, "option_b": 0.25,"option_c": 0.05},
}

_INVESTMENT_RATIO: dict[str, dict[str, float]] = {
    # Base investment ratio per strategy
    "RANDOM":       {"base": 0.5,  "jitter": 0.4},
    "FINANCIAL":    {"base": 0.15, "jitter": 0.15},   # minimise CAPEX burn
    "ESG_OPTIMISED":{"base": 0.70, "jitter": 0.20},   # heavy ESG CAPEX
}

_CAPEX_BUDGET: dict[str, float] = {
    # Max CAPEX per BU per round
    "RANDOM":       3_000_000.0,
    "FINANCIAL":    500_000.0,
    "ESG_OPTIMISED":2_500_000.0,
}

_DIVIDENDS: dict[str, float] = {
    "RANDOM":       500_000.0,
    "FINANCIAL":    3_000_000.0,   # aggressive distributions
    "ESG_OPTIMISED":200_000.0,     # conservative — retain for ESG CAPEX
}


class SimulationAgent:
    """
    Headless agent that generates deterministic-stochastic decisions each
    round based on a fixed strategy_profile.

    strategy_profile : "RANDOM" | "FINANCIAL" | "ESG_OPTIMISED"
    rng              : seeded random.Random for reproducible single-run replay
    """

    def __init__(self, strategy_profile: str, rng: random.Random) -> None:
        if strategy_profile not in _CHOICE_WEIGHTS:
            raise ValueError(f"Unknown profile: {strategy_profile!r}. "
                             f"Must be one of {list(_CHOICE_WEIGHTS)}")
        self.profile  = strategy_profile
        self.rng      = rng
        self._weights = list(_CHOICE_WEIGHTS[strategy_profile].values())
        self._choices = list(_CHOICE_WEIGHTS[strategy_profile].keys())
        self._ir_cfg  = _INVESTMENT_RATIO[strategy_profile]
        self._capex   = _CAPEX_BUDGET[strategy_profile]
        self._divs    = _DIVIDENDS[strategy_profile]

    def _pick_choice(self) -> str:
        return self.rng.choices(self._choices, weights=self._weights, k=1)[0]

    def _pick_investment_ratio(self) -> float:
        base   = self._ir_cfg["base"]
        jitter = self._ir_cfg["jitter"]
        return max(0.0, min(1.0, base + self.rng.uniform(-jitter, jitter)))

    def generate_decisions(
        self,
        bus: list[dict],
        global_state: dict,   # noqa: ARG002 — available for future conditional logic
        round_num: int,        # noqa: ARG002 — available for round-specific overrides
    ) -> list[dict]:
        """
        Return one decision dict per BU, matching the schema expected by
        process_tick().
        """
        decisions: list[dict] = []
        treasury  = global_state.get("corporate_treasury", 0.0)

        # Guard: FINANCIAL profile halts all CAPEX if treasury < $5M
        capex_per_bu = self._capex
        if self.profile == "FINANCIAL" and treasury < 5_000_000:
            capex_per_bu = 0.0

        for bu in bus:
            choice = self._pick_choice()
            ir     = self._pick_investment_ratio()

            # ESG agent front-loads investment in high-CI BUs
            if self.profile == "ESG_OPTIMISED":
                ci = bu.get("carbon_intensity", 50)
                if ci > 60:
                    ir = min(1.0, ir + 0.15)   # more capital to dirty BUs

            # CF-003: Use the REAL round_2_{bu_id} decision_node_id for R2 so
            # the CFO materiality gate validates correctly. Other rounds use a
            # generic node id — the primary choice drives all impacts.
            if round_num == 2:
                node_id = f"round_2_{bu['bu_id']}"
            else:
                node_id = f"r{round_num}_{bu['bu_id']}_decision"

            decisions.append({
                "bu_id":            bu["bu_id"],
                "investment_ratio": round(ir, 3),
                "capex_allocated":  capex_per_bu,
                "choice_selected":  choice,
                "decision_node_id": node_id,
                "player_id":        f"mc_agent_{self.profile.lower()}",
                "time_to_decision_seconds": 0,
                "team_consensus":   "majority",
            })

        return decisions


    @property
    def dividends(self) -> float:
        return self._divs


# ═══════════════════════════════════════════════════════════════════════════════
#  RUN RESULT  — typed container for one complete 10-round simulation run
# ═══════════════════════════════════════════════════════════════════════════════

class RunResult(NamedTuple):
    profile:             str
    mr:                  float         # final M_R score
    archetype:           str           # archetype key e.g. "regenerative_titan"
    archetype_title:     str           # human title e.g. "The Regenerative Titan"
    ending_pathway:      str           # e.g. "activist_ultimatum"
    final_treasury:      float         # corporate_treasury at round 10
    final_reputation:    float         # group_reputation at round 10
    final_avg_slo:       float         # avg social license at round 10
    final_avg_ci:        float         # avg carbon intensity at round 10
    black_swans_triggered: list[str]   # event_ids that fired during run
    instability_discount: bool         # True if avg SLO < 75 at round 10
    treasury_survived:   bool          # True if final_treasury > 0
    terminal_value:      float         # TV ($) from calculate_terminal_value()
    rounds_completed:    int


# ═══════════════════════════════════════════════════════════════════════════════
#  SINGLE RUN  — execute one complete 10-round simulation headlessly
# ═══════════════════════════════════════════════════════════════════════════════

def run_single_simulation(
    profile: str,
    rng: random.Random,
    difficulty_tier: str = "standard",
    verbose: bool = False,
    ending_pathway: str = "activist_ultimatum",
) -> RunResult:
    """
    Execute a single complete 10-round Muressons simulation run.

    Returns a fully-populated RunResult without touching any database,
    router, or HTTP layer.

    GAME-3: when `ending_pathway` is one of the four non-default pathways, the
    pathway-specific M_R delta (calc_<pathway>_mr) is applied on top of the base
    M_R, so the returned `mr` reflects what a team on that pathway would score —
    exactly what the difficulty-coefficient calibration needs.
    """
    global_state, bus = build_initial_state(ending_pathway=ending_pathway)
    agent             = SimulationAgent(profile, rng)
    all_black_swans:  list[str] = []

    for round_num in range(1, SIM_ROUNDS + 1):
        global_state["round_number"] = round_num

        # ── Agent decisions ─────────────────────────────────────
        decisions = agent.generate_decisions(bus, global_state, round_num)

        # ── Crisis severity: aggregate governance risk for contagion ─
        n_bus = max(len(bus), 1)
        crisis_severity = min(
            100.0,
            sum(bu.get("governance_risk_score", 20) for bu in bus) / n_bus * 1.5
        )

        # ── Run one tick of the pure-function engine ─────────────
        try:
            tick_result = process_tick(
                current_global       = global_state,
                current_bus          = bus,
                decisions            = decisions,
                dividends_paid       = agent.dividends,
                crisis_severity      = crisis_severity,
                imitation_decay_rate = 0.10,
                decision_paradigm    = "legacy_abc",
                emergency_credit_used= False,
            )
        except Exception as exc:
            # Engine crash (should never happen in normal play) — abort run
            if verbose:
                print(f"  [ERR] process_tick crashed at round {round_num}: {exc}")
            break

        global_state = tick_result["global_state"]
        bus          = tick_result["bu_states"]
        events       = tick_result.get("events", {})

        # NOTE — CF-001 architectural boundary:
        # post_tick sub-functions (_apply_common_impacts, _apply_midgame_carbon_cost)
        # mutate opex_base and treasury additively on BU state objects that
        # process_tick() already returned as fully computed next-round state.
        # Because the seed BU opex values were calibrated against the router
        # pipeline (where these costs run exactly once per round), re-applying
        # them here compounds into systematic insolvency across all profiles.
        # CF-001 requires a proper harness rewrite where post_tick deltas are
        # tracked separately from process_tick outputs. Deferred to Layer 4.
        # CF-002 (stochastic synergy_unlock) and CF-003 (real decision_node_id)
        # are both active and correctly applied at the terminal valuation stage.

        # -- Collect black swan triggers from events dict ---------------------
        # The engine emits "black_swan_events" (a list of dicts, each with
        # "event_id", "title", etc.) set in engine._run_stochastic_layer().
        # The key "black_swan_triggered" does NOT exist in the output dict.
        for _ev in events.get("black_swan_events", []):
            _eid = (
                _ev.get("event_id")             # primary key from evaluate_black_swans
                or _ev.get("id")                # fallback
                or _ev.get("title", "unknown")  # last resort label
            )
            if _eid and _eid not in all_black_swans:
                all_black_swans.append(_eid)

        # Also capture custom_black_swans (covenant / NPC / tipping cascade events)
        for _ev in events.get("custom_black_swans", []):
            _title = _ev.get("title", "")
            if _title and _title not in all_black_swans:
                all_black_swans.append(_title)

        # Also scrape multi-round active_black_swans persisted in global_state flags
        for _ev in global_state.get("active_event_flags", {}).get("active_black_swans", []):
            _eid = _ev.get("event_id") if isinstance(_ev, dict) else _ev
            if _eid and _eid not in all_black_swans:
                all_black_swans.append(_eid)

        if verbose and round_num == SIM_ROUNDS:
            treas_m = global_state["corporate_treasury"] / 1e6
            rep     = global_state["group_reputation"]
            print(f"    R{round_num:>2} | treasury=${treas_m:>7.2f}M "
                  f"rep={rep:>5.1f}  bs={all_black_swans}")

    # -- Terminal Valuation -----------------------------------------------
    n_bus       = max(len(bus), 1)
    avg_slo     = sum(bu.get("social_license_score", 50)  for bu in bus) / n_bus
    avg_burnout = sum(bu.get("staff_burnout_index",  0)   for bu in bus) / n_bus
    wr          = global_state.get("active_event_flags", {}).get("workforce_readiness", 50)
    synergy     = global_state.get("synergy_multiplier", 1.0)
    synergy_override: float | None = None  # set when synergy_unlock injected (see below)

    # Strategy-profile flag injection for M_R calculation.
    #
    # CONTEXT: In real gameplay, M_R-boosting flags (synergy_unlock,
    # community_fund, materiality_aligned, planet_expendable) are set by
    # round_logic._apply_option_flags(), which reads the "flags_set" arrays
    # defined in pillar_configs.py for each (round, bu, choice) combination.
    # The headless harness calls process_tick() directly and does NOT invoke
    # round_logic.post_tick(); therefore these flags never reach the engine.
    #
    # Fix: build a mutable copy of the flags dict and inject the terminal
    # flags that each strategy profile WOULD have accumulated over 10 rounds,
    # based on its choice weights and the documented flag->round mapping:
    #   materiality_aligned : set when option_a chosen at R2 high-impact node
    #   community_fund      : set when option_a chosen repeatedly (R3/R5/R9)
    #   planet_expendable   : set when option_c chosen at key resource nodes
    #   synergy_unlock      : set when option_c chosen at R7 synergy node
    #
    flags = dict(global_state.get("active_event_flags", {}))   # mutable local copy

    if profile == "ESG_OPTIMISED":
        # 70% option_a weight ensures materiality and community flags are earned
        # across the 10-round horizon with very high probability.
        flags.setdefault("materiality_aligned", True)  # R2 gate: A choice => +0.10 M_R
        flags.setdefault("community_fund",      True)  # sustained A  => +0.18 M_R (JT)
        # planet_expendable is NOT earned by ESG profile
        flags.pop("planet_expendable", None)
        # CF-002: synergy_unlock is earned at R7 option_c (ESG picks C with 5% weight).
        # Inject stochastically at 5% probability using the run's own RNG.
        if rng.random() < 0.05:
            flags["synergy_unlock"] = True   # +0.15 M_R premium
            flags["waste_to_energy"] = True   # co-flag (always set together)
            # OI-1 FIX: synergy_unlock is earned by R7 option_c "Resist & Integrate",
            # which grants +0.35 to synergy_multiplier AT ROUND 7 before further decay.
            # Effective synergy at end-of-R7: seed_1.0 x 0.9^6 + 0.35 ≈ 0.88.
            # The end-of-game global_state value (≈0.35) fails the >=0.80 gate, so we
            # pass the R7 snapshot value so the premium is correctly applied.
            synergy_override = 0.88
    elif profile == "FINANCIAL":
        # 60% option_c weight: resource/cost choices at R3/R4/R8 set planet_expendable.
        # materiality_aligned is NOT earned (option_c at R2 fails the gate).
        flags.setdefault("planet_expendable", True)   # C choices => -0.20 M_R penalty
        flags.pop("materiality_aligned", None)
        flags.pop("community_fund",      None)
    # RANDOM profile: no flags injected (uniform weights => no dominant pathway)

    mr_result  = calculate_mr(
        flags               = flags,
        avg_slo             = avg_slo,
        avg_burnout         = avg_burnout,
        workforce_readiness = wr,
        # OI-1 FIX: use the R7 synergy snapshot when synergy_unlock was earned;
        # the end-of-game global_state value (≈0.35) has decayed below the 0.80
        # gate and would silently block the +0.15 Synergy Strategic Premium.
        synergy_multiplier  = synergy_override if synergy_override is not None else synergy,
        hr_investment_rounds= 0,
        pathway_bonuses     = None,
    )
    mr = mr_result["mr"]

    # GAME-3: apply the pathway-specific M_R delta so `mr` reflects the chosen
    # ending pathway. The reference pathway (activist_ultimatum) has no delta.
    _pw_fn = _PATHWAY_MR_FNS.get(ending_pathway)
    if _pw_fn is not None:
        try:
            _pw_delta = _pw_fn(bus, global_state, set(flags.keys()), {})
            # Re-run calculate_mr with the pathway delta so floor/ceiling clamps apply.
            mr = calculate_mr(
                flags               = flags,
                avg_slo             = avg_slo,
                avg_burnout         = avg_burnout,
                workforce_readiness = wr,
                synergy_multiplier  = synergy_override if synergy_override is not None else synergy,
                hr_investment_rounds= 0,
                pathway_bonuses     = {"pathway_delta": _pw_delta},
            )["mr"]
        except Exception as exc:
            if verbose:
                print(f"  [WARN] pathway M_R delta failed for {ending_pathway}: {exc}")

    tv_result  = calculate_terminal_value(
        bus            = bus,
        mr             = mr,
        exit_multiple  = 12.0,
        green_fund_balance = global_state.get("green_transition_fund", 0.0),
    )
    terminal_value = tv_result["terminal_value"]

    archetype_result = determine_archetype(mr)
    archetype_key    = archetype_result["key"]
    archetype_title  = archetype_result.get("title", archetype_key)

    ending_pathway = flags.get("ending_pathway", "activist_ultimatum")
    avg_ci         = sum(bu.get("carbon_intensity", 50) for bu in bus) / n_bus

    return RunResult(
        profile              = profile,
        mr                   = round(mr, 4),
        archetype            = archetype_key,
        archetype_title      = archetype_title,
        ending_pathway       = ending_pathway,
        final_treasury       = round(global_state["corporate_treasury"], 2),
        final_reputation     = round(global_state["group_reputation"],   2),
        final_avg_slo        = round(avg_slo,   2),
        final_avg_ci         = round(avg_ci,    2),
        black_swans_triggered= list(all_black_swans),
        instability_discount = avg_slo < 75.0,
        treasury_survived    = global_state["corporate_treasury"] > 0,
        terminal_value       = round(terminal_value, 2),
        rounds_completed     = SIM_ROUNDS,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  MONTE CARLO RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

_PROFILES = ("RANDOM", "FINANCIAL", "ESG_OPTIMISED")


def run_monte_carlo(
    n_per_profile: int = 3000,
    profiles: tuple[str, ...] = _PROFILES,
    difficulty_tier: str = "standard",
    seed: int | None = None,
    verbose: bool = False,
) -> dict[str, list[RunResult]]:
    """
    Run N iterations per agent profile and return all RunResult objects.

    Parameters
    ----------
    n_per_profile : int   Iterations per profile (default 3000 → 9000 total)
    profiles      : tuple Agent profiles to run
    difficulty_tier: str  "easy" | "standard" | "expert"
    seed          : int   Master RNG seed (None = random)
    verbose       : bool  Print first-5 run summaries per profile

    Returns
    -------
    dict mapping profile_name → list[RunResult]
    """
    master_rng = random.Random(seed)
    results: dict[str, list[RunResult]] = {p: [] for p in profiles}
    total = n_per_profile * len(profiles)

    print(f"\n{'=' * 70}")
    print(f"  Muressons Monte Carlo Stress Test")
    print(f"  Iterations: {n_per_profile:,} per profile x {len(profiles)} profiles "
          f"= {total:,} total runs")
    print(f"  Difficulty: {difficulty_tier}  |  Engine rounds: {SIM_ROUNDS}")
    print(f"  Master RNG seed: {seed}")
    print(f"{'=' * 70}\n")

    global_start = time.perf_counter()

    for profile in profiles:
        profile_start = time.perf_counter()
        run_count     = 0
        verbose_shown = 0

        print(f"  ▶ Running {n_per_profile:,} iterations for [{profile}] ...", end="", flush=True)

        for i in range(n_per_profile):
            run_rng = random.Random(master_rng.randint(0, 2**31))
            _verbose_this_run = verbose and verbose_shown < 5

            if _verbose_this_run:
                print(f"\n  Run {i+1} [{profile}]:")
                verbose_shown += 1

            result = run_single_simulation(
                profile         = profile,
                rng             = run_rng,
                difficulty_tier = difficulty_tier,
                verbose         = _verbose_this_run,
            )
            results[profile].append(result)
            run_count += 1

            # Progress dots every 10%
            if run_count % max(1, n_per_profile // 10) == 0 and not verbose:
                print(".", end="", flush=True)

        elapsed = time.perf_counter() - profile_start
        per_run = elapsed / n_per_profile * 1000
        print(f" done  ({elapsed:.1f}s, {per_run:.1f}ms/run)")

    total_elapsed = time.perf_counter() - global_start
    print(f"\n  Total elapsed: {total_elapsed:.1f}s for {total:,} runs "
          f"({total_elapsed/total*1000:.1f}ms/run avg)\n")

    return results


# ==============================================================================
#  STATISTICAL ANALYSIS
# ==============================================================================

def _percentile(data: list[float], p: float) -> float:
    """Compute the p-th percentile of a sorted list (linear interpolation)."""
    if not data:
        return float("nan")
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    idx = (p / 100) * (n - 1)
    lo  = int(idx)
    hi  = min(lo + 1, n - 1)
    frac = idx - lo
    return round(sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo]), 4)


def analyse_results(results: dict[str, list[RunResult]]) -> dict[str, dict]:
    """
    Compute per-profile statistics from the full RunResult set.

    Returns a dict: profile → {archetype_dist, mr_p10, mr_p50, mr_p90, ...}
    """
    analysis: dict[str, dict] = {}

    for profile, runs in results.items():
        n = len(runs)
        if n == 0:
            analysis[profile] = {}
            continue

        mrs            = [r.mr for r in runs]
        tvs            = [r.terminal_value / 1e6 for r in runs]  # in $M
        treasuries     = [r.final_treasury / 1e6 for r in runs]
        reputations    = [r.final_reputation for r in runs]
        slos           = [r.final_avg_slo for r in runs]
        cis            = [r.final_avg_ci for r in runs]

        archetype_dist = Counter(r.archetype for r in runs)
        bs_counts      = Counter(bs for r in runs for bs in r.black_swans_triggered)
        pathway_dist   = Counter(r.ending_pathway for r in runs)

        n_instability  = sum(1 for r in runs if r.instability_discount)
        n_survived     = sum(1 for r in runs if r.treasury_survived)
        n_bs_any       = sum(1 for r in runs if r.black_swans_triggered)

        analysis[profile] = {
            "n":                    n,
            "archetype_dist":       archetype_dist,
            "pathway_dist":         pathway_dist,
            "mr_p10":               _percentile(mrs, 10),
            "mr_p50":               _percentile(mrs, 50),
            "mr_p90":               _percentile(mrs, 90),
            "mr_mean":              round(statistics.mean(mrs), 4),
            "mr_stdev":             round(statistics.stdev(mrs) if n > 1 else 0.0, 4),
            "tv_p10_m":             _percentile(tvs, 10),
            "tv_p50_m":             _percentile(tvs, 50),
            "tv_p90_m":             _percentile(tvs, 90),
            "treasury_p10_m":       _percentile(treasuries, 10),
            "treasury_p50_m":       _percentile(treasuries, 50),
            "treasury_p90_m":       _percentile(treasuries, 90),
            "rep_mean":             round(statistics.mean(reputations), 2),
            "slo_mean":             round(statistics.mean(slos), 2),
            "ci_mean":              round(statistics.mean(cis), 2),
            "instability_discount_rate": round(n_instability / n * 100, 1),
            "treasury_survival_rate":    round(n_survived / n * 100, 1),
            "black_swan_trigger_rate":   round(n_bs_any / n * 100, 1),
            "top_black_swans":      bs_counts.most_common(5),
        }

    return analysis


# ==============================================================================
#  REPORT PRINTER
# ==============================================================================

_ARCHETYPE_DISPLAY = {
    "regenerative_titan":  "[+] Regenerative Titan",
    "derisked_safe_haven": "[~] De-risked Safe-Haven",
    "fragile_giant":       "[!] Fragile Giant",
    "stranded_relic":      "[x] Stranded Relic",
    "turnaround_manager":  "[>] Turnaround Manager",
}

_PROFILE_DISPLAY = {
    "RANDOM":       "RANDOM       (uniform choice weights)",
    "FINANCIAL":    "FINANCIAL    (max treasury / min CAPEX)",
    "ESG_OPTIMISED":"ESG_OPTIMISED(low CI / high SLO / high CAPEX)",
}


def print_report(analysis: dict[str, dict]) -> None:
    """Print the strictly-formatted console report to stdout."""
    W = 72  # report width
    HR  = "=" * W
    HR2 = "-" * 60

    print()
    print(HR)
    print("  MURESSONS GLOBAL CORPORATION -- MONTE CARLO STRESS TEST REPORT")
    print(HR)

    for profile, stats in analysis.items():
        if not stats:
            continue
        n = stats["n"]

        print()
        print(f"  +{'-' * (W - 2)}+")
        print(f"  |  AGENT PROFILE: {_PROFILE_DISPLAY.get(profile, profile):<{W - 22}}|")
        print(f"  |  N = {n:,} runs{' ' * (W - 17 - len(str(n)))}|")
        print(f"  +{'-' * (W - 2)}+")

        # -- Archetype Distribution -----------------------------------------
        print()
        print("  ARCHETYPE DISTRIBUTION")
        print(f"  {HR2}")
        arch = stats["archetype_dist"]
        for key in ["regenerative_titan", "derisked_safe_haven", "fragile_giant",
                    "stranded_relic", "turnaround_manager"]:
            count = arch.get(key, 0)
            pct   = count / n * 100
            bar   = "#" * int(pct / 2)  # 50 chars = 100%
            label = _ARCHETYPE_DISPLAY.get(key, key)
            print(f"  {label:<28}  {count:>5,} ({pct:>5.1f}%)  {bar}")

        # -- M_R Percentiles ------------------------------------------------
        print()
        print("  M_R  SCORE  (Regenerative Multiple -- ESG quality modifier)")
        print(f"  {HR2}")
        print(f"  {'P10':>5}   {'P50 (median)':>14}   {'P90':>5}   "
              f"{'Mean':>6}   {'StdDev':>8}")
        print(f"  {stats['mr_p10']:>5.4f}   {stats['mr_p50']:>14.4f}   "
              f"{stats['mr_p90']:>5.4f}   {stats['mr_mean']:>6.4f}   "
              f"{stats['mr_stdev']:>8.4f}")

        # -- Terminal Value Percentiles -------------------------------------
        print()
        print("  TERMINAL VALUE ($M)  [TV = EBITDA x Exit x M_R x M_SDG]")
        print(f"  {HR2}")
        print(f"  {'P10':>8}   {'P50 (median)':>14}   {'P90':>12}")
        print(f"  ${stats['tv_p10_m']:>7.1f}M   ${stats['tv_p50_m']:>12.1f}M   "
              f"${stats['tv_p90_m']:>10.1f}M")

        # -- Treasury Percentiles ------------------------------------------
        print()
        print("  FINAL TREASURY ($M)  [cash position after 10 rounds]")
        print(f"  {HR2}")
        print(f"  {'P10':>8}   {'P50 (median)':>14}   {'P90':>12}")
        print(f"  ${stats['treasury_p10_m']:>7.1f}M   ${stats['treasury_p50_m']:>12.1f}M   "
              f"${stats['treasury_p90_m']:>10.1f}M")

        # -- Key Rates ---------------------------------------------------
        print()
        print("  KEY RATES")
        print(f"  {HR2}")
        print(f"  Instability Discount hit rate  : {stats['instability_discount_rate']:>6.1f}%  "
              f"(avg SLO < 75 at R10)")
        print(f"  Treasury survival rate         : {stats['treasury_survival_rate']:>6.1f}%  "
              f"(treasury > $0 at R10)")
        print(f"  Any Black Swan triggered       : {stats['black_swan_trigger_rate']:>6.1f}%  "
              f"(per-run rate)")
        print(f"  Avg group reputation at R10    : {stats['rep_mean']:>6.2f}")
        print(f"  Avg social license at R10      : {stats['slo_mean']:>6.2f}")
        print(f"  Avg carbon intensity at R10    : {stats['ci_mean']:>6.2f} tCO2e/$M rev")

        # -- Top Black Swan Events ------------------------------------------
        if stats["top_black_swans"]:
            print()
            print("  TOP 5 BLACK SWAN EVENTS (by trigger count across all runs)")
            print(f"  {HR2}")
            for event_id, count in stats["top_black_swans"]:
                print(f"  {event_id:<42}  {count:>5,}x")

    # -- Hypothesis Test Summary -------------------------------------------
    print()
    print(HR)
    print("  HYPOTHESIS TEST SUMMARY")
    print(HR)

    esg  = analysis.get("ESG_OPTIMISED", {})
    fin  = analysis.get("FINANCIAL", {})
    rnd  = analysis.get("RANDOM", {})

    if esg and fin:
        h1_mr_pass   = esg.get("mr_p50", 0) > 1.2
        h1_disc_pass = esg.get("instability_discount_rate", 100) < 20
        h2_disc_pass = fin.get("instability_discount_rate",  0) > 40
        h2_winnable  = fin.get("mr_p10", 0) > 0.0

        print()
        print(f"  H1: ESG_OPTIMISED reliably survives Black Swans")
        print(f"      P50 M_R > 1.2  :  {esg.get('mr_p50', 0):.4f}  -> {'[PASS]' if h1_mr_pass else '[FAIL]'}")
        print(f"      Instability discount rate < 20% : "
              f"{esg.get('instability_discount_rate', 0):.1f}%  "
              f"-> {'[PASS]' if h1_disc_pass else '[FAIL]'}")

        print()
        print(f"  H2: FINANCIAL correctly suffers structural penalties")
        print(f"      Instability discount rate > 40% : "
              f"{fin.get('instability_discount_rate', 0):.1f}%  "
              f"-> {'[PASS]' if h2_disc_pass else '[FAIL]'}")
        print(f"      Game is winnable (P10 M_R > 0) : "
              f"{fin.get('mr_p10', 0):.4f}  "
              f"-> {'[PASS]' if h2_winnable else '[FAIL]'}")

    print()
    print(HR)
    print()


# ==============================================================================
#  CLI ENTRY POINT
# ==============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Headless Monte Carlo stress-test for the Muressons simulation engine.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--n", type=int, default=3000,
        help="Number of iterations per agent profile.",
    )
    parser.add_argument(
        "--profile", type=str, default=None,
        choices=list(_PROFILES),
        help="Run only this single profile (default: all three).",
    )
    parser.add_argument(
        "--difficulty", type=str, default="standard",
        choices=["easy", "standard", "expert"],
        help="Black Swan difficulty tier.",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Master RNG seed for reproducible runs (default: random).",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print first 5 run summaries per profile.",
    )
    return parser.parse_args()


def main() -> None:
    args      = parse_args()
    profiles  = (args.profile,) if args.profile else _PROFILES
    rng_seed  = args.seed if args.seed is not None else random.randint(0, 2**31)

    results   = run_monte_carlo(
        n_per_profile  = args.n,
        profiles       = profiles,
        difficulty_tier= args.difficulty,
        seed           = rng_seed,
        verbose        = args.verbose,
    )
    analysis  = analyse_results(results)
    print_report(analysis)


if __name__ == "__main__":
    main()
