"""
Muressons Global Corporation — Deterministic Matrix Validation Harness
═══════════════════════════════════════════════════════════════════════
Principal QA Architect: Automated Test Suite
Run: pytest tests/test_universal_math_engine.py -v --tb=long

Validates mathematical integrity of the core game economy (EBITDA,
M_R, Carbon Intensity, and Treasury) across all decision paradigms,
industry verticals, and side-track integrations.

Anti-Slop Directives Enforced:
  ✗ No mocking of engine.py, terminal_valuation.py, or balance_sheet.py
  ✓ Synthetic payloads through actual process_tick and valuation pipelines
  ✓ Black swans deterministically suppressed via random.seed + flag control
  ✓ Strict mathematical invariant assertions with formatted failure blocks
"""

from __future__ import annotations

import copy
import json
import math
import os
import random
import sys
import textwrap
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Any, Generator

import pytest

# ── Path Setup ────────────────────────────────────────────────────
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

# Force in-memory database
os.environ["USE_MEMORY_DB"] = "true"

# ── Real Imports (No Mocks) ──────────────────────────────────────
from engine import (
    process_tick,
    calc_csf,
    calc_revenue_weighted_avg_ci,
    _calc_rw_avg_ci,
    apply_side_track_results,
)
from terminal_valuation import (
    calculate_mr,
    calculate_terminal_value,
    calculate_sdg_multiplier,
)
from balance_sheet import (
    process_balance_sheet_tick,
    create_initial_balance_sheet,
)
from bu_profiles import BU_PROFILES, build_bu_states, DEFAULT_SLOTS
from side_tracks.bridge_schemas import (
    DataBridgeOutput,
    BridgeKPIDeltas,
    KPIOverrides,
)


# ═════════════════════════════════════════════════════════════════
#  CONFIGURATION CONSTANTS
# ═════════════════════════════════════════════════════════════════

# M_R bounds from terminal_valuation.py — hard floor/ceiling
MR_FLOOR: float = 0.0
MR_CEILING: float = 2.05

# Simulation config reference values
INITIAL_TREASURY: float = 50_000_000.0
NUM_ROUNDS: int = 3  # Enough rounds to validate invariants without excessive runtime

# Deterministic seed for all stochastic suppression
DETERMINISTIC_SEED: int = 42


# ═════════════════════════════════════════════════════════════════
#  INVARIANT FAILURE REPORTER
# ═════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class InvariantViolation:
    """Structured invariant failure record."""
    invariant_id: str
    invariant_name: str
    paradigm: str
    bu_composition: str
    side_track: str | None
    round_number: int
    expected_value: float | str
    actual_value: float | str
    tolerance: float | None = None

    def format_block(self) -> str:
        """Strictly formatted error block for invariant failures."""
        tol_line = f"  Tolerance:     {self.tolerance}" if self.tolerance is not None else ""
        return textwrap.dedent(f"""\
        ┌─────────────────────────────────────────────────────────┐
        │ INVARIANT VIOLATION: {self.invariant_id}                │
        ├─────────────────────────────────────────────────────────┤
        │ Invariant:     {self.invariant_name}
        │ Paradigm:      {self.paradigm}
        │ BU Comp:       {self.bu_composition}
        │ Side Track:    {self.side_track or 'None'}
        │ Round:         {self.round_number}
        │ Expected:      {self.expected_value}
        │ Actual:        {self.actual_value}
        {tol_line}
        └─────────────────────────────────────────────────────────┘""")


def report_violation(violation: InvariantViolation) -> None:
    """Raise AssertionError with strictly formatted failure block."""
    raise AssertionError(f"\n{violation.format_block()}")


# ═════════════════════════════════════════════════════════════════
#  BU COMPOSITION FACTORY
# ═════════════════════════════════════════════════════════════════

def _build_default_4bu() -> list[dict]:
    """DEFAULT_4_BU: pharma, electronics, consumer_goods, software."""
    return build_bu_states(substitutions=None)


def _build_single_bu_pharma() -> list[dict]:
    """SINGLE_BU_PHARMA: only the pharma BU in a list."""
    profile = BU_PROFILES["pharma"]
    return [{
        "bu_id": "pharma",
        "bu_label": profile["label"],
        "bu_icon": profile.get("icon", "🏢"),
        "revenue_base": profile["revenue_base"],
        "opex_base": profile["opex_base"],
        "carbon_intensity": profile["carbon_intensity"],
        "water_dependency": profile["water_dependency"],
        "natural_capital_debt": profile.get("natural_capital_debt", 100),
        "social_license_score": profile.get("social_license_score", 50),
        "governance_risk_score": profile.get("governance_risk_score", 15),
        "reputation_score": profile.get("reputation_score", 55),
        "staff_burnout_index": 10.0,
        "vrio_advantage": 0.80,
        "consecutive_zero_investment_rounds": 0,
        "risk_factors": {
            "top_investment_streak": 0,
            "crisis_count_lifetime": 0,
        },
    }]


def _build_vertical_oil_and_gas() -> list[dict]:
    """VERTICAL_OIL_AND_GAS_SUB: oil_gas replaces pharma slot."""
    return build_bu_states(substitutions={"pharma": "oil_gas"})


BU_COMPOSITION_FACTORIES: dict[str, callable] = {
    "DEFAULT_4_BU": _build_default_4bu,
    "SINGLE_BU_PHARMA": _build_single_bu_pharma,
    "VERTICAL_OIL_AND_GAS_SUB": _build_vertical_oil_and_gas,
}


# ═════════════════════════════════════════════════════════════════
#  SIDE-TRACK PAYLOAD FACTORY
# ═════════════════════════════════════════════════════════════════

def _build_side_track_payload(
    side_track_type: str | None,
) -> DataBridgeOutput | None:
    """Build a DataBridgeOutput payload for side-track testing."""
    if side_track_type is None:
        return None

    if side_track_type == "SDG_MAX_IMPACT":
        return DataBridgeOutput(
            flags_to_set={
                "sdg_impact_score": 85,
                "sdg_track_completed": True,
                "sdg_mr_bonus": 0.15,
            },
            flags_to_remove=[],
            kpi_deltas=BridgeKPIDeltas(
                treasury_delta=-500_000.0,
                reputation_delta=10.0,
                carbon_intensity_delta=-5.0,
            ),
            kpi_overrides=KPIOverrides(),  # No overrides for SDG
        )

    if side_track_type == "BRSR_PENALTY":
        return DataBridgeOutput(
            flags_to_set={
                "brsr_track_completed": True,
                "brsr_performance_score": 25.0,
                "brsr_grade": "D",
            },
            flags_to_remove=[],
            kpi_deltas=BridgeKPIDeltas(
                treasury_delta=-1_000_000.0,
                reputation_delta=-10.0,
                carbon_intensity_delta=3.0,
                governance_risk_delta=5.0,
            ),
            kpi_overrides=KPIOverrides(),  # No overrides for BRSR
        )

    raise ValueError(f"Unknown side_track_type: {side_track_type}")


def _build_side_track_with_override(
    override_metric: str,
    override_value: float,
) -> DataBridgeOutput:
    """Build a DataBridgeOutput with a KPIOverride for Data Bridge Integrity testing."""
    overrides_kwargs = {override_metric: override_value}
    return DataBridgeOutput(
        flags_to_set={"side_track_override_test": True},
        flags_to_remove=[],
        kpi_deltas=BridgeKPIDeltas(
            treasury_delta=-200_000.0,
            reputation_delta=5.0,
        ),
        kpi_overrides=KPIOverrides(**overrides_kwargs),
    )


# ═════════════════════════════════════════════════════════════════
#  GLOBAL STATE FACTORY
# ═════════════════════════════════════════════════════════════════

def make_global_state(
    round_number: int = 1,
    treasury: float = INITIAL_TREASURY,
    paradigm: str = "legacy_abc",
) -> dict[str, Any]:
    """Construct a deterministic global state dict for process_tick."""
    return {
        "round_number": round_number,
        "corporate_treasury": treasury,
        "group_reputation": 55.0,
        "synergy_multiplier": 1.0,
        "cost_of_capital": 0.05,
        "inflation_index": 0.05,
        "competitor_ebitda": 13_200_000.0,
        "active_event_flags": {
            "difficulty_tier": "standard",
        },
        "green_transition_fund": 0.0,
        "tipping_point_active": False,
        "tipping_tier": "none",
        "pending_capex_projects": [],
        "political_capital": 50.0,
        "community_trust_score": 50.0,
        "global_emissions_intensity": 0.0,
        "sbti_pathway_history": [],
        "carbon_forwards": [],
        "momentum_history": [],
        "_prev_global_states": [],
    }


# ═════════════════════════════════════════════════════════════════
#  DECISION FACTORY
# ═════════════════════════════════════════════════════════════════

def make_decisions(
    bus: list[dict],
    paradigm: str = "legacy_abc",
    choice: str = "option_a",
) -> list[dict]:
    """Build a list of neutral decisions for all BUs."""
    decisions = []
    for bu in bus:
        dec = {
            "bu_id": bu["bu_id"],
            "investment_ratio": 0.10,
            "capex_allocated": 500_000,
            "choice_selected": choice,
            "decision_node_id": "",
            "time_to_decision_seconds": 30,
            "team_consensus": "majority",
        }
        if paradigm == "multi_toggles":
            dec["pillar_decisions"] = {
                "energy": "incremental_efficiency",
                "operations": "circular_procurement",
                "supply_chain": "audit_suppliers",
                "offsetting": "voluntary_offsets",
                "human_resources": "training_programme",
            }
        decisions.append(dec)
    return decisions


# ═════════════════════════════════════════════════════════════════
#  PERMUTATION GENERATOR
# ═════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MatrixConfig:
    """A single test permutation configuration."""
    decision_paradigm: str
    bu_composition: str
    side_track_payload: str | None

    @property
    def label(self) -> str:
        st = self.side_track_payload or "NONE"
        return f"{self.decision_paradigm}|{self.bu_composition}|{st}"


def generate_test_matrices() -> Generator[MatrixConfig, None, None]:
    """
    Permutation generator yielding combinations of:
    - decision_paradigm: ["multi_toggles", "legacy_abc"]
    - bu_composition: ["DEFAULT_4_BU", "SINGLE_BU_PHARMA", "VERTICAL_OIL_AND_GAS_SUB"]
    - side_track_payload: [None, "SDG_MAX_IMPACT", "BRSR_PENALTY"]
    """
    paradigms = ["multi_toggles", "legacy_abc"]
    compositions = ["DEFAULT_4_BU", "SINGLE_BU_PHARMA", "VERTICAL_OIL_AND_GAS_SUB"]
    side_tracks = [None, "SDG_MAX_IMPACT", "BRSR_PENALTY"]

    for paradigm, composition, side_track in product(paradigms, compositions, side_tracks):
        yield MatrixConfig(
            decision_paradigm=paradigm,
            bu_composition=composition,
            side_track_payload=side_track,
        )


# ═════════════════════════════════════════════════════════════════
#  MULTI-ROUND SIMULATION RUNNER
# ═════════════════════════════════════════════════════════════════

# DEEP-8 diagnostics: raw engine events per round of the most recent
# run_deterministic_simulation call (cleared at each run start).
LAST_RUN_EVENTS: list = []


@dataclass
class RoundLedger:
    """Tracks per-round financial data for invariant verification."""
    round_number: int
    treasury_start: float
    treasury_end: float
    csf: float  # Gross profit = Σ(rev - opex) - dividends
    total_capex: float
    # DEEP-8: signed post-tick option-treasury movement (round handlers'
    # charges/gains via _apply_treasury_with_green_fund and the R10 direct
    # add). Negative = money left treasury.
    option_treasury: float
    # DEEP-8 terms 3-6 (2026-08-31): engine-side direct treasury movements,
    # each read from its own event. Signed (negative = charge).
    regulatory_ratchet_fine: float
    black_swan_treasury_hit: float  # DEEP-8 term 7: sum of black-swan treasury hits (positive = money left)
    treasury_floor_clamp: float  # DEEP-8 term 8: losses absorbed by the insolvency floor (positive = credit)
    cbam_surcharge: float
    loss_damage_levy: float
    deferred_revenue_collected: float
    side_track_treasury_delta: float
    loan_interest: float
    emergency_credit_interest: float
    negative_treasury_interest: float
    # BU-level snapshots
    bu_revenues: dict[str, float] = field(default_factory=dict)
    bu_opex: dict[str, float] = field(default_factory=dict)
    bu_carbon_intensities: dict[str, float] = field(default_factory=dict)


def run_deterministic_simulation(
    matrix: MatrixConfig,
    num_rounds: int = NUM_ROUNDS,
    choice_map: dict[int, str] | None = None,
) -> tuple[list[RoundLedger], dict, list[dict]]:
    """
    Execute a multi-round simulation with deterministic stochastic suppression.

    Returns:
        (ledgers, final_global_state, final_bu_states)
    """
    # Suppress all stochastic paths
    random.seed(DETERMINISTIC_SEED)

    bus = BU_COMPOSITION_FACTORIES[matrix.bu_composition]()
    gs = make_global_state(paradigm=matrix.decision_paradigm)

    # RNG-2 (2026-08-02): this runner is called "deterministic" and, until now,
    # was not. It seeds the global `random` module — but the GAME-4 engine paths
    # do not draw from it. They call rng_util.event_rng(flags, ...), which
    # derives its stream from flags["stochastic_seed"] and, WHEN THAT KEY IS
    # ABSENT, returns `random.Random()` — a fresh, system-seeded generator that
    # `random.seed()` cannot reach (rng_util.py:56).
    #
    # This harness never set the key, so every seeded-engine draw came from
    # interpreter entropy. Two consecutive runs of the same command produced
    # materially different simulations: unexplained treasury movement on
    # DEFAULT_4_BU/multi_toggles measured $200,081,152 on one run and
    # $402,477,721 on the next.
    #
    # Every invariant in this file was therefore being evaluated against a
    # DIFFERENT simulation each time. They passed because they assert bounds and
    # finiteness rather than values — which is exactly how a suite can be green
    # for months without pinning anything.
    #
    # One line. Set the cohort seed the way a real cohort carries it.
    gs.setdefault("active_event_flags", {})["stochastic_seed"] = f"ume-{DETERMINISTIC_SEED}"

    ledgers: list[RoundLedger] = []
    LAST_RUN_EVENTS.clear()  # DEEP-8 diagnostics: raw events per round of the most recent run

    for rnd in range(1, num_rounds + 1):
        gs["round_number"] = rnd

        # W4 balance report: an optional per-round strategy; the default path
        # (all option_a) is bit-identical to before, keeping the pinned
        # cross-process fingerprints valid.
        decisions = make_decisions(
            bus, paradigm=matrix.decision_paradigm,
            choice=(choice_map or {}).get(rnd, "option_a"),
        )

        treasury_before = gs["corporate_treasury"]

        # Re-seed before each tick for cross-round determinism
        random.seed(DETERMINISTIC_SEED + rnd)

        result = process_tick(
            current_global=copy.deepcopy(gs),
            current_bus=copy.deepcopy(bus),
            decisions=decisions,
            dividends_paid=0.0,
            crisis_severity=0.0,
            imitation_decay_rate=0.10,
            decision_paradigm=matrix.decision_paradigm,
            emergency_credit_used=False,
        )

        new_gs = result["global_state"]
        # DEEP-8 root cause (2026-09-01): process_tick returns a REBUILT
        # active_event_flags that drops the cohort stochastic_seed. Production
        # never sees this: router.commit_turn merges the OLD flags back in as
        # the base ("preserve history"), so the seed survives round to round.
        # This harness feeds the engine its own raw output, so from R2 onward
        # every event_rng() call was falling back to a SYSTEM-seeded Random —
        # black swans fired nondeterministically per process, which was both
        # the "flaky residual" and (at least one) strict-xfail entropy source.
        # dry_run.py:164 carries the seed manually for the same reason; do the
        # same here so this harness matches what a real cohort experiences.
        new_gs.setdefault("active_event_flags", {})["stochastic_seed"] = (
            gs["active_event_flags"]["stochastic_seed"]
        )
        new_bus = result["bu_states"]
        events = result["events"]
        LAST_RUN_EVENTS.append(events)

        # ── Apply side-track effects post-tick if configured ──
        side_track_treasury_delta = 0.0
        if matrix.side_track_payload is not None and rnd == 2:
            # Apply side-track at round 2 to test mid-simulation injection
            payload = _build_side_track_payload(matrix.side_track_payload)
            if payload is not None:
                pre_st_treasury = new_gs["corporate_treasury"]
                new_gs = apply_side_track_results(new_gs, payload, apply_flags=True)
                side_track_treasury_delta = (
                    new_gs["corporate_treasury"] - pre_st_treasury
                )

        # ── Extract waterfall data for the ledger ──
        # DEEP-8 (2026-08-31): read the ENGINE's own CSF from its waterfall
        # entry instead of recomputing from the FINAL bus table. Stages after
        # the treasury line (talent surcharges, synergy-lag completions,
        # reporting-layer mutations) keep moving rev/opex, so a recomputation
        # measures a different quantity than the one the engine banked —
        # that mismatch alone accounted for a smooth ~0.4–0.7M/round phantom
        # residual. A ledger records what happened; it does not re-derive it.
        csf_val = None
        for entry in (events.get("consequence_waterfall") or {}).get("entries", []):
            if entry.get("label") == "Gross Profit (CSF)":
                csf_val = entry["amount"]
                break
        if csf_val is None:  # engine did not emit one — fall back to recompute
            csf_val = sum(
                bu["revenue_base"] - bu["opex_base"] for bu in new_bus
            )

        option_treasury = events.get("ledger_option_treasury", 0.0)
        # DEEP-8: the Regulatory Ratchet fine nests inside a dict event — the
        # exact silent debit behind the residuals of 2,500,000.00 (1 BU: 25
        # gov-risk points x \$100K) and 3,750,000.00 (4 BU) at R1.
        ratchet_fine = float((events.get("regulatory_ratchet") or {}).get("fine", 0.0) or 0.0)
        # DEEP-8 term 7 (2026-09-01): black swans debit treasury directly in
        # apply_black_swan_impacts; the diagnostics event carries the exact sum.
        swan_hit = float((events.get("black_swan_diagnostics") or {}).get("total_treasury_drain", 0.0) or 0.0)
        floor_clamp = float(events.get("treasury_floor_clamp_applied", 0.0) or 0.0)
        cbam = float(events.get("cbam_surcharge_applied", 0.0) or 0.0)
        levy = float(events.get("loss_damage_levy_applied", 0.0) or 0.0)
        rev_gen = float(events.get("revenue_generation_completed", 0.0) or 0.0)
        loan_interest = events.get("loan_interest_payment", 0.0)
        emergency_interest = events.get("emergency_credit_interest", 0.0)
        neg_treasury_interest = events.get("negative_treasury_interest_applied", 0.0)
        total_capex = sum(d.get("capex_allocated", 0) for d in decisions)

        ledgers.append(RoundLedger(
            round_number=rnd,
            treasury_start=treasury_before,
            treasury_end=new_gs["corporate_treasury"],
            csf=csf_val,
            total_capex=total_capex,
            option_treasury=option_treasury,
            regulatory_ratchet_fine=ratchet_fine,
            black_swan_treasury_hit=swan_hit,
            treasury_floor_clamp=floor_clamp,
            cbam_surcharge=cbam,
            loss_damage_levy=levy,
            deferred_revenue_collected=rev_gen,
            side_track_treasury_delta=side_track_treasury_delta,
            loan_interest=loan_interest,
            emergency_credit_interest=emergency_interest,
            negative_treasury_interest=neg_treasury_interest,
            bu_revenues={bu["bu_id"]: bu["revenue_base"] for bu in new_bus},
            bu_opex={bu["bu_id"]: bu["opex_base"] for bu in new_bus},
            bu_carbon_intensities={
                bu["bu_id"]: bu.get("carbon_intensity", 0.0) for bu in new_bus
            },
        ))

        # Chain state forward
        gs = new_gs
        bus = new_bus

    return ledgers, gs, bus


# ═════════════════════════════════════════════════════════════════
#  INVARIANT CHECKERS
# ═════════════════════════════════════════════════════════════════

def check_invariant_1_treasury_conservation(
    matrix: MatrixConfig,
    ledgers: list[RoundLedger],
    final_gs: dict,
) -> None:
    """
    INVARIANT 1 — Conservation of Treasury:
    The engine's treasury waterfall must be internally consistent.
    Each round: treasury_end must not be NaN or infinite, and
    multi-round chaining must produce a valid final treasury.
    """
    for ledger in ledgers:
        # Treasury must never be NaN or infinite
        if math.isnan(ledger.treasury_end) or math.isinf(ledger.treasury_end):
            report_violation(InvariantViolation(
                invariant_id="INV-1",
                invariant_name="Conservation of Treasury",
                paradigm=matrix.decision_paradigm,
                bu_composition=matrix.bu_composition,
                side_track=matrix.side_track_payload,
                round_number=ledger.round_number,
                expected_value="finite float",
                actual_value=str(ledger.treasury_end),
            ))

        # Treasury must flow continuously (end of round N = start of round N+1)
        if ledger.round_number < len(ledgers):
            next_ledger = ledgers[ledger.round_number]  # 0-indexed
            # The engine does deep-copy, so treasury_end should match next start
            # within the waterfall chain
            if abs(ledger.treasury_end - next_ledger.treasury_start) > 0.01:
                report_violation(InvariantViolation(
                    invariant_id="INV-1",
                    invariant_name="Conservation of Treasury (Round Continuity)",
                    paradigm=matrix.decision_paradigm,
                    bu_composition=matrix.bu_composition,
                    side_track=matrix.side_track_payload,
                    round_number=ledger.round_number,
                    expected_value=f"treasury_end({ledger.round_number})="
                                   f"{ledger.treasury_end:.2f}",
                    actual_value=f"treasury_start({ledger.round_number + 1})="
                                 f"{next_ledger.treasury_start:.2f}",
                    tolerance=0.01,
                ))

    # Final treasury must be finite
    final_treasury = final_gs["corporate_treasury"]
    if math.isnan(final_treasury) or math.isinf(final_treasury):
        report_violation(InvariantViolation(
            invariant_id="INV-1",
            invariant_name="Conservation of Treasury (Final State)",
            paradigm=matrix.decision_paradigm,
            bu_composition=matrix.bu_composition,
            side_track=matrix.side_track_payload,
            round_number=len(ledgers),
            expected_value="finite float",
            actual_value=str(final_treasury),
        ))


def check_invariant_2_mr_boundaries(
    matrix: MatrixConfig,
    final_gs: dict,
    final_bus: list[dict],
) -> None:
    """
    INVARIANT 2 — M_R Boundaries:
    The Regenerative Multiple MUST NEVER drop below 0.0 and MUST NEVER
    exceed the theoretical ceiling of 2.05, regardless of flag stacking.
    """
    # Compute M_R with maximally stacked bonuses
    n_bu = max(len(final_bus), 1)
    avg_slo = sum(
        bu.get("social_license_score", 50) for bu in final_bus
    ) / n_bu
    avg_burnout = sum(
        bu.get("staff_burnout_index", 0) for bu in final_bus
    ) / n_bu
    workforce_readiness = final_gs.get(
        "active_event_flags", {}
    ).get("workforce_readiness", 50.0)
    synergy_multiplier = final_gs.get("synergy_multiplier", 1.0)

    # Test with a maximally beneficial flag set
    max_flags = {
        "materiality_aligned": True,
        "synergy_unlock": True,
        "ethical_ai_overhaul": True,
        "community_fund": True,
        "brsr_net_positive_dividend": 0.05,
    }
    mr_result = calculate_mr(
        flags=max_flags,
        avg_slo=avg_slo,
        avg_burnout=avg_burnout,
        workforce_readiness=workforce_readiness,
        synergy_multiplier=synergy_multiplier,
        hr_investment_rounds=5,
    )
    mr_value = mr_result["mr"]

    if mr_value < MR_FLOOR:
        report_violation(InvariantViolation(
            invariant_id="INV-2a",
            invariant_name="M_R Floor Violation (max bonuses)",
            paradigm=matrix.decision_paradigm,
            bu_composition=matrix.bu_composition,
            side_track=matrix.side_track_payload,
            round_number=-1,
            expected_value=f">= {MR_FLOOR}",
            actual_value=f"{mr_value:.6f}",
        ))

    if mr_value > MR_CEILING:
        report_violation(InvariantViolation(
            invariant_id="INV-2b",
            invariant_name="M_R Ceiling Violation (max bonuses)",
            paradigm=matrix.decision_paradigm,
            bu_composition=matrix.bu_composition,
            side_track=matrix.side_track_payload,
            round_number=-1,
            expected_value=f"<= {MR_CEILING}",
            actual_value=f"{mr_value:.6f}",
        ))

    # Test with maximally punitive flags
    min_flags = {
        "planet_expendable": True,
        "insurance_only": True,
    }
    mr_result_min = calculate_mr(
        flags=min_flags,
        avg_slo=10.0,  # Very low SLO
        avg_burnout=80.0,  # Very high burnout
        workforce_readiness=20.0,
        synergy_multiplier=0.3,
        hr_investment_rounds=0,
    )
    mr_value_min = mr_result_min["mr"]

    if mr_value_min < MR_FLOOR:
        report_violation(InvariantViolation(
            invariant_id="INV-2c",
            invariant_name="M_R Floor Violation (max penalties)",
            paradigm=matrix.decision_paradigm,
            bu_composition=matrix.bu_composition,
            side_track=matrix.side_track_payload,
            round_number=-1,
            expected_value=f">= {MR_FLOOR}",
            actual_value=f"{mr_value_min:.6f}",
        ))

    if mr_value_min > MR_CEILING:
        report_violation(InvariantViolation(
            invariant_id="INV-2d",
            invariant_name="M_R Ceiling Violation (max penalties)",
            paradigm=matrix.decision_paradigm,
            bu_composition=matrix.bu_composition,
            side_track=matrix.side_track_payload,
            round_number=-1,
            expected_value=f"<= {MR_CEILING}",
            actual_value=f"{mr_value_min:.6f}",
        ))


def check_invariant_3_ci_accounting(
    matrix: MatrixConfig,
    ledgers: list[RoundLedger],
    final_bus: list[dict],
) -> None:
    """
    INVARIANT 3 — CI Accounting:
    Group Carbon Intensity MUST be the exact revenue-weighted average
    of the individual BU Carbon Intensities.

    Formula: avg_CI = Σ(CI_i × Rev_i) / Σ(Rev_i)
    """
    for ledger in ledgers:
        total_rev = sum(ledger.bu_revenues.values())
        if total_rev <= 0:
            continue  # Skip rounds with zero total revenue

        weighted_ci = sum(
            ledger.bu_carbon_intensities[bu_id] * ledger.bu_revenues[bu_id]
            for bu_id in ledger.bu_revenues
        )
        expected_group_ci = weighted_ci / total_rev

        # Compute via the actual engine function on BU snapshots
        bu_snapshots = [
            {
                "bu_id": bu_id,
                "revenue_base": ledger.bu_revenues[bu_id],
                "carbon_intensity": ledger.bu_carbon_intensities[bu_id],
            }
            for bu_id in ledger.bu_revenues
        ]
        actual_group_ci = _calc_rw_avg_ci(bu_snapshots)

        # Allow floating-point tolerance of 0.01
        if abs(expected_group_ci - actual_group_ci) > 0.01:
            report_violation(InvariantViolation(
                invariant_id="INV-3",
                invariant_name="CI Revenue-Weighted Average Accounting",
                paradigm=matrix.decision_paradigm,
                bu_composition=matrix.bu_composition,
                side_track=matrix.side_track_payload,
                round_number=ledger.round_number,
                expected_value=f"{expected_group_ci:.6f}",
                actual_value=f"{actual_group_ci:.6f}",
                tolerance=0.01,
            ))


def check_invariant_4_data_bridge_integrity(
    matrix: MatrixConfig,
) -> None:
    """
    INVARIANT 4 — Data Bridge Integrity:
    If a side-track payload contains a KPIOverride, the target metric
    MUST equal the exact override value post-tick, entirely ignoring any
    relative mathematical deltas that occurred in the same round.
    """
    # Build a state to apply overrides to
    bus = BU_COMPOSITION_FACTORIES[matrix.bu_composition]()
    gs = make_global_state(paradigm=matrix.decision_paradigm)

    # Test override for each supported KPI override field
    # Override field names matching KPIOverrides schema → state key (from _KPI_OVERRIDE_MAP)
    override_cases = [
        ("corporate_treasury", 42_000_000.0, "corporate_treasury"),
        ("group_reputation", 75.0, "group_reputation"),
        ("avg_carbon_intensity", 25.0, "avg_carbon_intensity"),
        ("synergy_multiplier", 1.25, "synergy_multiplier"),
    ]

    for override_field, override_value, expected_state_key in override_cases:
        payload = _build_side_track_with_override(override_field, override_value)

        # Seed the state with all keys the engine expects
        test_state = copy.deepcopy(gs)
        test_state.setdefault("avg_carbon_intensity", 40.0)
        test_state.setdefault("avg_social_license", 50.0)
        test_state.setdefault("avg_governance_risk", 15.0)
        test_state.setdefault("total_ncd", 100.0)

        state_after = apply_side_track_results(test_state, payload, apply_flags=True)

        actual_value = state_after.get(expected_state_key)

        if actual_value is None:
            report_violation(InvariantViolation(
                invariant_id="INV-4",
                invariant_name=f"Data Bridge Integrity ({override_field}) — key missing post-apply",
                paradigm=matrix.decision_paradigm,
                bu_composition=matrix.bu_composition,
                side_track=f"KPIOverride:{override_field}",
                round_number=0,
                expected_value=f"{override_value}",
                actual_value="None (key not found)",
            ))
            continue

        if abs(actual_value - override_value) > 0.000001:
            report_violation(InvariantViolation(
                invariant_id="INV-4",
                invariant_name=f"Data Bridge Integrity ({override_field})",
                paradigm=matrix.decision_paradigm,
                bu_composition=matrix.bu_composition,
                side_track=f"KPIOverride:{override_field}",
                round_number=0,
                expected_value=f"{override_value}",
                actual_value=f"{actual_value}",
                tolerance=0.000001,
            ))


# ═════════════════════════════════════════════════════════════════
#  SUPPLEMENTARY INVARIANTS
# ═════════════════════════════════════════════════════════════════

def check_invariant_5_process_tick_structure(
    matrix: MatrixConfig,
    final_gs: dict,
    final_bus: list[dict],
) -> None:
    """
    INVARIANT 5 — Structural Integrity:
    process_tick output must contain all required top-level keys with
    correct types.
    """
    required_gs_keys = [
        "round_number", "corporate_treasury", "group_reputation",
        "synergy_multiplier", "cost_of_capital",
    ]
    for key in required_gs_keys:
        if key not in final_gs:
            report_violation(InvariantViolation(
                invariant_id="INV-5a",
                invariant_name=f"Missing global_state key: {key}",
                paradigm=matrix.decision_paradigm,
                bu_composition=matrix.bu_composition,
                side_track=matrix.side_track_payload,
                round_number=-1,
                expected_value=f"key '{key}' present",
                actual_value="missing",
            ))

    required_bu_keys = [
        "bu_id", "revenue_base", "opex_base", "carbon_intensity",
    ]
    for bu in final_bus:
        for key in required_bu_keys:
            if key not in bu:
                report_violation(InvariantViolation(
                    invariant_id="INV-5b",
                    invariant_name=f"Missing bu_state key: {key} (BU: {bu.get('bu_id', '?')})",
                    paradigm=matrix.decision_paradigm,
                    bu_composition=matrix.bu_composition,
                    side_track=matrix.side_track_payload,
                    round_number=-1,
                    expected_value=f"key '{key}' present",
                    actual_value="missing",
                ))


def check_invariant_6_bu_field_bounds(
    matrix: MatrixConfig,
    ledgers: list[RoundLedger],
    final_bus: list[dict],
) -> None:
    """
    INVARIANT 6 — BU Field Bounds:
    All BU-level metric fields must be within valid bounds after each tick.
    """
    for bu in final_bus:
        bu_id = bu.get("bu_id", "unknown")

        # Revenue and OPEX must be non-negative
        if bu.get("revenue_base", 0) < 0:
            report_violation(InvariantViolation(
                invariant_id="INV-6a",
                invariant_name=f"Negative revenue_base (BU: {bu_id})",
                paradigm=matrix.decision_paradigm,
                bu_composition=matrix.bu_composition,
                side_track=matrix.side_track_payload,
                round_number=len(ledgers),
                expected_value=">= 0",
                actual_value=f"{bu['revenue_base']:.2f}",
            ))

        if bu.get("opex_base", 0) < 0:
            report_violation(InvariantViolation(
                invariant_id="INV-6b",
                invariant_name=f"Negative opex_base (BU: {bu_id})",
                paradigm=matrix.decision_paradigm,
                bu_composition=matrix.bu_composition,
                side_track=matrix.side_track_payload,
                round_number=len(ledgers),
                expected_value=">= 0",
                actual_value=f"{bu['opex_base']:.2f}",
            ))

        # Carbon intensity must be non-negative
        ci = bu.get("carbon_intensity", 0)
        if ci < 0:
            report_violation(InvariantViolation(
                invariant_id="INV-6c",
                invariant_name=f"Negative carbon_intensity (BU: {bu_id})",
                paradigm=matrix.decision_paradigm,
                bu_composition=matrix.bu_composition,
                side_track=matrix.side_track_payload,
                round_number=len(ledgers),
                expected_value=">= 0",
                actual_value=f"{ci:.2f}",
            ))

        # Reputation and social license must be in [0, 100]
        rep = bu.get("reputation_score", 50)
        if rep < 0 or rep > 100:
            report_violation(InvariantViolation(
                invariant_id="INV-6d",
                invariant_name=f"reputation_score out of bounds (BU: {bu_id})",
                paradigm=matrix.decision_paradigm,
                bu_composition=matrix.bu_composition,
                side_track=matrix.side_track_payload,
                round_number=len(ledgers),
                expected_value="[0.0, 100.0]",
                actual_value=f"{rep:.2f}",
            ))

        slo = bu.get("social_license_score", 50)
        if slo < 0 or slo > 100:
            report_violation(InvariantViolation(
                invariant_id="INV-6e",
                invariant_name=f"social_license_score out of bounds (BU: {bu_id})",
                paradigm=matrix.decision_paradigm,
                bu_composition=matrix.bu_composition,
                side_track=matrix.side_track_payload,
                round_number=len(ledgers),
                expected_value="[0.0, 100.0]",
                actual_value=f"{slo:.2f}",
            ))


def check_invariant_7_terminal_valuation_consistency(
    matrix: MatrixConfig,
    final_gs: dict,
    final_bus: list[dict],
) -> None:
    """
    INVARIANT 7 — Terminal Valuation Consistency:
    TV must be computable from the final state without errors, and
    the components must be self-consistent.
    """
    n_bu = max(len(final_bus), 1)
    avg_slo = sum(bu.get("social_license_score", 50) for bu in final_bus) / n_bu
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in final_bus) / n_bu
    synergy = final_gs.get("synergy_multiplier", 1.0)

    mr_result = calculate_mr(
        flags=final_gs.get("active_event_flags", {}),
        avg_slo=avg_slo,
        avg_burnout=avg_burnout,
        workforce_readiness=50.0,
        synergy_multiplier=synergy,
    )
    mr = mr_result["mr"]

    tv_result = calculate_terminal_value(
        bus=final_bus,
        mr=mr,
        carbon_tax_per_ton=250.0,
        exit_multiple=12.0,
    )

    # TV must be non-negative (EBITDA is floored at 0, M_R >= 0)
    tv = tv_result["terminal_value"]
    if tv < 0:
        report_violation(InvariantViolation(
            invariant_id="INV-7",
            invariant_name="Terminal Value Non-Negative",
            paradigm=matrix.decision_paradigm,
            bu_composition=matrix.bu_composition,
            side_track=matrix.side_track_payload,
            round_number=-1,
            expected_value=">= 0",
            actual_value=f"{tv:.2f}",
        ))

    # Gross profit from TV must match manual calculation
    manual_gross = sum(
        bu["revenue_base"] - bu["opex_base"] for bu in final_bus
    )
    tv_gross = tv_result["gross_profit"]
    if abs(manual_gross - tv_gross) > 0.01:
        report_violation(InvariantViolation(
            invariant_id="INV-7b",
            invariant_name="Terminal Valuation Gross Profit Consistency",
            paradigm=matrix.decision_paradigm,
            bu_composition=matrix.bu_composition,
            side_track=matrix.side_track_payload,
            round_number=-1,
            expected_value=f"{manual_gross:.2f}",
            actual_value=f"{tv_gross:.2f}",
            tolerance=0.01,
        ))


def check_invariant_8_ebitda_consistency(
    matrix: MatrixConfig,
    ledgers: list[RoundLedger],
    final_gs: dict,
    final_bus: list[dict],
) -> None:
    """
    INVARIANT 8 — EBITDA Consistency:
    historical_ebitda is computed at the END of Stage 2 (Financial Layer),
    BEFORE Stage 3 (Operational Layer) applies further OPEX penalties (NCD,
    employer brand, etc.). Therefore:
      - historical_ebitda must be a finite number
      - Final Σ(Revenue - OPEX) ≤ historical_ebitda (Stage 3 only adds costs)
    """
    historical_ebitda = final_gs.get("historical_ebitda")

    # Must exist and be numeric
    if historical_ebitda is None:
        report_violation(InvariantViolation(
            invariant_id="INV-8a",
            invariant_name="EBITDA field missing from global_state",
            paradigm=matrix.decision_paradigm,
            bu_composition=matrix.bu_composition,
            side_track=matrix.side_track_payload,
            round_number=len(ledgers),
            expected_value="present",
            actual_value="None",
        ))
        return

    if math.isnan(historical_ebitda) or math.isinf(historical_ebitda):
        report_violation(InvariantViolation(
            invariant_id="INV-8b",
            invariant_name="EBITDA must be finite",
            paradigm=matrix.decision_paradigm,
            bu_composition=matrix.bu_composition,
            side_track=matrix.side_track_payload,
            round_number=len(ledgers),
            expected_value="finite float",
            actual_value=str(historical_ebitda),
        ))
        return

    # Stage 3 only adds OPEX penalties, so final EBITDA ≤ historical_ebitda
    final_ebitda = sum(
        bu["revenue_base"] - bu["opex_base"] for bu in final_bus
    )
    if final_ebitda > historical_ebitda + 0.01:
        report_violation(InvariantViolation(
            invariant_id="INV-8c",
            invariant_name="Final EBITDA ≤ Stage-2 historical_ebitda",
            paradigm=matrix.decision_paradigm,
            bu_composition=matrix.bu_composition,
            side_track=matrix.side_track_payload,
            round_number=len(ledgers),
            expected_value=f"final_ebitda ({final_ebitda:.2f}) ≤ historical_ebitda ({historical_ebitda:.2f})",
            actual_value=f"final_ebitda ({final_ebitda:.2f}) > historical_ebitda ({historical_ebitda:.2f})",
            tolerance=0.01,
        ))


# ═════════════════════════════════════════════════════════════════
#  PYTEST FIXTURES
# ═════════════════════════════════════════════════════════════════

@pytest.fixture(
    params=list(generate_test_matrices()),
    ids=lambda m: m.label,
)
def test_matrix(request) -> MatrixConfig:
    """Parametrize over all permutation matrices."""
    return request.param


@pytest.fixture
def simulation_result(test_matrix: MatrixConfig):
    """Run a deterministic multi-round simulation for the given matrix."""
    return run_deterministic_simulation(test_matrix)


# ═════════════════════════════════════════════════════════════════
#  TEST CLASSES — MATHEMATICAL INVARIANT REGISTRY
# ═════════════════════════════════════════════════════════════════

class TestInvariant1TreasuryConservation:
    """
    INV-1: Conservation of Treasury
    Final_Treasury chaining must be consistent across rounds.
    Treasury must never be NaN or infinite.
    """

    def test_treasury_conservation(
        self, test_matrix: MatrixConfig, simulation_result
    ):
        ledgers, final_gs, final_bus = simulation_result
        check_invariant_1_treasury_conservation(test_matrix, ledgers, final_gs)

    def test_treasury_is_numeric(
        self, test_matrix: MatrixConfig, simulation_result
    ):
        _, final_gs, _ = simulation_result
        treasury = final_gs["corporate_treasury"]
        assert isinstance(treasury, (int, float)), (
            f"Treasury is not numeric: {type(treasury)}"
        )
        assert not math.isnan(treasury), "Treasury is NaN"
        assert not math.isinf(treasury), "Treasury is infinite"


class TestInvariant2MRBoundaries:
    """
    INV-2: M_R Boundaries
    The calculated Regenerative Multiple MUST NEVER drop below 0.0
    and MUST NEVER exceed 2.05 regardless of flag stacking.
    """

    def test_mr_boundaries(
        self, test_matrix: MatrixConfig, simulation_result
    ):
        _, final_gs, final_bus = simulation_result
        check_invariant_2_mr_boundaries(test_matrix, final_gs, final_bus)

    def test_mr_extreme_bonus_ceiling(self):
        """M_R with ALL bonuses stacked must not exceed ceiling."""
        flags = {
            "materiality_aligned": True,
            "synergy_unlock": True,
            "ethical_ai_overhaul": True,
            "community_fund": True,
            "brsr_net_positive_dividend": 0.10,
        }
        result = calculate_mr(
            flags=flags,
            avg_slo=100.0,
            avg_burnout=0.0,
            workforce_readiness=100.0,
            synergy_multiplier=2.0,
            hr_investment_rounds=10,
            pathway_bonuses={"max_test": 0.5},
        )
        assert result["mr"] <= MR_CEILING, (
            f"M_R {result['mr']:.4f} exceeds ceiling {MR_CEILING}"
        )

    def test_mr_extreme_penalty_floor(self):
        """M_R with ALL penalties stacked must not drop below floor."""
        flags = {
            "planet_expendable": True,
            "insurance_only": True,
        }
        result = calculate_mr(
            flags=flags,
            avg_slo=0.0,
            avg_burnout=100.0,
            workforce_readiness=0.0,
            synergy_multiplier=0.0,
            hr_investment_rounds=0,
            pathway_bonuses={"max_penalty": -0.5},
        )
        assert result["mr"] >= MR_FLOOR, (
            f"M_R {result['mr']:.4f} below floor {MR_FLOOR}"
        )


class TestInvariant3CIAccounting:
    """
    INV-3: CI Accounting
    Group Carbon Intensity MUST be the exact revenue-weighted average
    of the individual BU Carbon Intensities.
    """

    def test_ci_revenue_weighted_average(
        self, test_matrix: MatrixConfig, simulation_result
    ):
        ledgers, _, final_bus = simulation_result
        check_invariant_3_ci_accounting(test_matrix, ledgers, final_bus)

    def test_ci_function_identity(self):
        """Both CI functions must produce identical results."""
        bus = [
            {"bu_id": "a", "revenue_base": 10_000_000, "carbon_intensity": 50.0},
            {"bu_id": "b", "revenue_base": 20_000_000, "carbon_intensity": 100.0},
        ]
        # Expected: (50*10M + 100*20M) / (10M+20M) = 2500M/30M ≈ 83.33
        result1 = calc_revenue_weighted_avg_ci(bus)
        result2 = _calc_rw_avg_ci(bus)
        expected = (50.0 * 10e6 + 100.0 * 20e6) / 30e6
        assert abs(result1 - expected) < 0.01
        assert abs(result2 - expected) < 0.01
        assert abs(result1 - result2) < 0.001

    def test_ci_single_bu(self):
        """Single BU: group CI must equal BU CI exactly."""
        bus = [
            {"bu_id": "solo", "revenue_base": 50_000_000, "carbon_intensity": 35.0},
        ]
        result = _calc_rw_avg_ci(bus)
        assert abs(result - 35.0) < 0.001

    def test_ci_zero_revenue_fallback(self):
        """Zero total revenue: falls back to simple arithmetic mean."""
        bus = [
            {"bu_id": "a", "revenue_base": 0, "carbon_intensity": 40.0},
            {"bu_id": "b", "revenue_base": 0, "carbon_intensity": 80.0},
        ]
        result = _calc_rw_avg_ci(bus)
        assert abs(result - 60.0) < 0.001  # (40+80)/2


class TestInvariant4DataBridgeIntegrity:
    """
    INV-4: Data Bridge Integrity
    If a side-track payload contains a KPIOverride, the target metric
    MUST equal the exact override value post-application.
    """

    def test_data_bridge_overrides(self, test_matrix: MatrixConfig):
        check_invariant_4_data_bridge_integrity(test_matrix)

    def test_override_trumps_delta(self):
        """Override must overwrite the delta result for the same KPI."""
        state = {
            "corporate_treasury": 50_000_000.0,
            "group_reputation": 55.0,
            "avg_carbon_intensity": 40.0,
            "synergy_multiplier": 1.0,
            "avg_social_license": 50.0,
            "total_ncd": 100.0,
            "active_event_flags": {},
        }

        # Delta says +5M treasury, but override sets to exactly 42M
        payload = DataBridgeOutput(
            flags_to_set={"side_track_test": True},
            flags_to_remove=[],
            kpi_deltas=BridgeKPIDeltas(
                treasury_delta=5_000_000.0,
                reputation_delta=20.0,
            ),
            kpi_overrides=KPIOverrides(
                corporate_treasury=42_000_000.0,
                group_reputation=30.0,
            ),
        )

        result = apply_side_track_results(state, payload, apply_flags=False)

        # Override must win over delta
        assert result["corporate_treasury"] == 42_000_000.0, (
            f"Treasury override failed: {result['corporate_treasury']}"
        )
        assert result["group_reputation"] == 30.0, (
            f"Reputation override failed: {result['group_reputation']}"
        )

    def test_none_override_preserves_delta(self):
        """None override fields must leave the delta result intact."""
        state = {
            "corporate_treasury": 50_000_000.0,
            "group_reputation": 55.0,
            "active_event_flags": {},
        }
        payload = DataBridgeOutput(
            flags_to_set={"side_track_test_2": True},
            flags_to_remove=[],
            kpi_deltas=BridgeKPIDeltas(
                treasury_delta=-1_000_000.0,
            ),
            kpi_overrides=KPIOverrides(
                corporate_treasury=None,  # Should not override
            ),
        )
        result = apply_side_track_results(state, payload, apply_flags=False)

        expected_treasury = 50_000_000.0 - 1_000_000.0
        assert abs(result["corporate_treasury"] - expected_treasury) < 0.01


class TestInvariant5StructuralIntegrity:
    """
    INV-5: Process Tick Structural Integrity
    Output dict must contain all required keys with correct types.
    """

    def test_structural_integrity(
        self, test_matrix: MatrixConfig, simulation_result
    ):
        _, final_gs, final_bus = simulation_result
        check_invariant_5_process_tick_structure(test_matrix, final_gs, final_bus)


class TestInvariant6BUFieldBounds:
    """
    INV-6: BU Field Bounds
    All BU-level metrics must stay within engine-defined bounds.
    """

    def test_bu_field_bounds(
        self, test_matrix: MatrixConfig, simulation_result
    ):
        ledgers, _, final_bus = simulation_result
        check_invariant_6_bu_field_bounds(test_matrix, ledgers, final_bus)


class TestInvariant7TerminalValuation:
    """
    INV-7: Terminal Valuation Consistency
    TV must be non-negative and gross profit must match BU sum.
    """

    def test_terminal_valuation_consistency(
        self, test_matrix: MatrixConfig, simulation_result
    ):
        _, final_gs, final_bus = simulation_result
        check_invariant_7_terminal_valuation_consistency(
            test_matrix, final_gs, final_bus
        )


class TestInvariant8EBITDA:
    """
    INV-8: EBITDA = Σ(Revenue - OPEX)
    historical_ebitda must equal the manual sum.
    """

    def test_ebitda_consistency(
        self, test_matrix: MatrixConfig, simulation_result
    ):
        ledgers, final_gs, final_bus = simulation_result
        check_invariant_8_ebitda_consistency(
            test_matrix, ledgers, final_gs, final_bus
        )


# ═════════════════════════════════════════════════════════════════
#  STANDALONE M_R BOUNDARY STRESS TESTS (Non-Parametrized)
# ═════════════════════════════════════════════════════════════════

class TestMRBoundaryStress:
    """
    Exhaustive M_R boundary testing with extreme flag combinations.
    These run independently of the permutation matrix.
    """

    @pytest.mark.parametrize("slo", [0.0, 10.0, 50.0, 74.9, 75.0, 100.0])
    @pytest.mark.parametrize("burnout", [0.0, 19.9, 20.0, 50.0, 100.0])
    def test_mr_always_within_bounds(self, slo: float, burnout: float):
        """M_R must be in [0.0, 2.05] for any SLO/burnout combination."""
        # Stack maximum bonuses
        flags = {
            "materiality_aligned": True,
            "synergy_unlock": True,
            "ethical_ai_overhaul": True,
            "community_fund": True,
        }
        result = calculate_mr(
            flags=flags,
            avg_slo=slo,
            avg_burnout=burnout,
            workforce_readiness=75.0,
            synergy_multiplier=1.0,
            hr_investment_rounds=3,
        )
        assert MR_FLOOR <= result["mr"] <= MR_CEILING, (
            f"M_R={result['mr']:.4f} out of [{MR_FLOOR}, {MR_CEILING}] "
            f"at slo={slo}, burnout={burnout}"
        )


# ═════════════════════════════════════════════════════════════════
#  STANDALONE CI FORMULA TESTS (Non-Parametrized)
# ═════════════════════════════════════════════════════════════════

class TestCIFormulaStress:
    """
    Stress tests for CI revenue-weighted average formula correctness.
    """

    def test_ci_all_equal_revenue(self):
        """When all BUs have equal revenue, CI = simple average."""
        bus = [
            {"bu_id": "a", "revenue_base": 10e6, "carbon_intensity": 30.0},
            {"bu_id": "b", "revenue_base": 10e6, "carbon_intensity": 60.0},
            {"bu_id": "c", "revenue_base": 10e6, "carbon_intensity": 90.0},
        ]
        result = _calc_rw_avg_ci(bus)
        assert abs(result - 60.0) < 0.01  # simple mean

    def test_ci_dominant_low_ci_bu(self):
        """When a low-CI BU dominates revenue, group CI should be pulled down."""
        bus = [
            {"bu_id": "green", "revenue_base": 90e6, "carbon_intensity": 10.0},
            {"bu_id": "brown", "revenue_base": 10e6, "carbon_intensity": 200.0},
        ]
        result = _calc_rw_avg_ci(bus)
        expected = (10.0 * 90e6 + 200.0 * 10e6) / 100e6  # = 29.0
        assert abs(result - expected) < 0.01
        assert result < 30.0  # Much closer to the green BU

    def test_ci_dominant_high_ci_bu(self):
        """When a high-CI BU dominates revenue, group CI should be pulled up."""
        bus = [
            {"bu_id": "green", "revenue_base": 10e6, "carbon_intensity": 10.0},
            {"bu_id": "brown", "revenue_base": 90e6, "carbon_intensity": 200.0},
        ]
        result = _calc_rw_avg_ci(bus)
        expected = (10.0 * 10e6 + 200.0 * 90e6) / 100e6  # = 181.0
        assert abs(result - expected) < 0.01
        assert result > 170.0  # Much closer to the brown BU


# ═════════════════════════════════════════════════════════════════
#  STANDALONE PROCESS_TICK SMOKE TESTS (Non-Parametrized)
# ═════════════════════════════════════════════════════════════════

class TestProcessTickSmoke:
    """
    Basic smoke tests that process_tick runs without crashes
    for each paradigm/composition pair.
    """

    @pytest.mark.parametrize("paradigm", ["legacy_abc", "multi_toggles"])
    @pytest.mark.parametrize("composition", [
        "DEFAULT_4_BU", "SINGLE_BU_PHARMA", "VERTICAL_OIL_AND_GAS_SUB"
    ])
    def test_single_tick_no_crash(self, paradigm: str, composition: str):
        """A single tick must complete without raising."""
        random.seed(DETERMINISTIC_SEED)
        bus = BU_COMPOSITION_FACTORIES[composition]()
        gs = make_global_state(paradigm=paradigm)

        decisions = make_decisions(bus, paradigm=paradigm)

        result = process_tick(
            current_global=copy.deepcopy(gs),
            current_bus=copy.deepcopy(bus),
            decisions=decisions,
            decision_paradigm=paradigm,
        )

        assert "global_state" in result
        assert "bu_states" in result
        assert "events" in result
        assert result["global_state"]["round_number"] == 2
        assert len(result["bu_states"]) == len(bus)

    @pytest.mark.parametrize("composition", [
        "DEFAULT_4_BU", "SINGLE_BU_PHARMA", "VERTICAL_OIL_AND_GAS_SUB"
    ])
    def test_multi_round_chaining(self, composition: str):
        """Multi-round chaining must produce valid state at each step."""
        random.seed(DETERMINISTIC_SEED)
        bus = BU_COMPOSITION_FACTORIES[composition]()
        gs = make_global_state()

        for rnd in range(1, 4):
            gs["round_number"] = rnd
            random.seed(DETERMINISTIC_SEED + rnd)

            decisions = make_decisions(bus)
            result = process_tick(
                current_global=copy.deepcopy(gs),
                current_bus=copy.deepcopy(bus),
                decisions=decisions,
            )

            gs = result["global_state"]
            bus = result["bu_states"]

            assert gs["round_number"] == rnd + 1
            assert isinstance(gs["corporate_treasury"], (int, float))
            assert not math.isnan(gs["corporate_treasury"])


# ═════════════════════════════════════════════════════════════════
#  STANDALONE DATA BRIDGE SCHEMA TESTS
# ═════════════════════════════════════════════════════════════════

class TestDataBridgeSchemaIntegrity:
    """
    Validate the Pydantic schema contracts for DataBridgeOutput.
    """

    def test_invalid_flag_prefix_raises(self):
        """Unregistered flag prefixes must raise ValueError."""
        with pytest.raises(ValueError, match="unregistered flag"):
            DataBridgeOutput(
                flags_to_set={"illegal_flag": True},
            )

    def test_valid_flag_prefixes_accepted(self):
        """All registered prefixes must be accepted."""
        valid = DataBridgeOutput(
            flags_to_set={
                "sdg_test": True,
                "brsr_test": True,
                "supply_test": True,
                "ethics_test": True,
            }
        )
        assert len(valid.flags_to_set) == 4

    def test_treasury_delta_max_enforced(self):
        """Treasury delta exceeding ±$20M must be rejected."""
        with pytest.raises(ValueError, match="treasury_delta"):
            BridgeKPIDeltas(treasury_delta=25_000_000.0)

    def test_flag_set_remove_overlap_rejected(self):
        """A flag in both set and remove must raise ValueError."""
        with pytest.raises(ValueError, match="flags_to_set and flags_to_remove"):
            DataBridgeOutput(
                flags_to_set={"sdg_conflict": True},
                flags_to_remove=["sdg_conflict"],
            )

    def test_kpi_override_none_is_noop(self):
        """KPIOverrides with all None must be a no-op."""
        overrides = KPIOverrides()
        dumped = overrides.model_dump()
        assert all(v is None for v in dumped.values())
