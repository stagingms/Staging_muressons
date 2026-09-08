"""Muressons — the Monte Carlo stress harness (Phase 5 of the dead-flag remediation).

WHY THIS EXISTS, AND WHY THE COVERING ARRAY IS NOT ENOUGH
    tests/golden_matrix_harness.py drives a COVERING set: seven fixed paths chosen
    so that every (round, option) pair and every named cross-round combination is
    exercised at least once. That is the right instrument for "does this mechanic
    fire?" and it is the wrong one for "what can a team actually reach?".

    Phase 5 has to re-derive the M_R ceilings, the 2.05 clamp and the archetype
    thresholds, and every one of those is a claim about a DISTRIBUTION — where the
    mass sits, where the tails are, how often a boundary is crossed. Seven points
    cannot answer that. This module samples the decision space instead, on the SAME
    `drive` loop the fixtures use, because a stress harness with its own copy of
    the production sequence would measure a different engine from the one the
    fixtures pin — the mistake Phase 3 spent a day undoing.

WHAT IT VARIES, AND WHY EACH ONE
    choices     3^10 = 59,049 legacy paths. Sampled uniformly; the covering array
                touches 7 of them.
    spend       The solvency axis. The financial oracle's own calibration note
                records that a 0.3-investment run at $1M capex per BU is insolvent
                by round 4, and Phase 4 measured the distress cascade appearing and
                disappearing with it. A distribution that holds spend fixed
                describes one bank balance, not a game.
    seed        Each run gets its own stochastic_seed string, so seeded events vary.
    pathway     The ending pathway is session configuration, not a decision, and
                four of the five M_R pathway calculators run for no path unless one
                is chosen. Sampling it is the only way their premiums enter the
                distribution at all.
    swans       Sampled BOTH ways. The committed fixtures are captured with black
                swans off so their deltas are attributable to decisions; a
                THRESHOLD re-derived from a swan-free distribution would describe a
                game nobody plays.

PAIRED, NOT TWO SAMPLES
    Every spec is run under both rule sets and the outcomes are returned as a pair.
    Comparing two independent samples of a high-variance simulation would need an
    enormous N to see a 1% shift; comparing the SAME game under both rule sets
    isolates the rules exactly, and the residual variance is zero by construction.

WHAT IT IS NOT
    Not a fixture. Nothing here is committed as a golden master: the sample is a
    pure function of (n, seed) so any run is reproducible, but its purpose is
    measurement, not regression. The regression instrument is the covering array.
"""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import golden_matrix_harness as H   # noqa: E402

# The five ending pathways. activist_ultimatum is the platform default and the
# only one the covering array ran until Phase 3 added two directed cases.
PATHWAYS = ("activist_ultimatum", "climate_black_swan", "stakeholder_revolt",
            "hostile_takeover", "regulatory_shutdown")

# The solvency grid. Spans the financial oracle's measured insolvency script
# (0.3 investment, $1M capex per BU) through to the comfortable band the golden
# paths sit in.
INVEST_LEVELS = (0.1, 0.3, 0.5, 0.7, 0.9)
CAPEX_LEVELS = (0, 250_000, 500_000, 1_000_000, 2_000_000)

_BU_IDS = ("pharma", "electronics", "consumer_goods", "software")
_OPTIONS = ("option_a", "option_b", "option_c")

_SWANS_OFF = {"black_swan_events_enabled": False, "decision_timer_enabled": False}
_SWANS_ON = {"black_swan_events_enabled": True, "decision_timer_enabled": False}


@dataclass
class Outcome:
    """One finished game, as the engine graded it."""
    label: str
    rules_version: str
    swans: bool
    pathway: str
    invest: float
    capex: int
    # ── the graded numbers ────────────────────────────────────────
    mr: float = 0.0
    mr_raw: float = 0.0
    mr_ceiling_clamped: bool = False
    mr_floor_clamped: bool = False
    terminal_value: float = 0.0
    exit_multiple: float = 0.0
    wacc: float = 0.0
    archetype: str = ""
    profile: str = ""
    # ── the quantities Phase 4's switches move ────────────────────
    sct: float = 0.0
    sdg_index: float = 0.0
    m_sdg: float = 1.0
    treasury: float = 0.0
    equity_wiped_out: bool = False
    bonuses: tuple = ()
    failed: str = ""


def _finale(gs: dict) -> dict:
    return gs.get("active_event_flags") or {}


def sample_specs(n: int, seed: int, swans: bool = False) -> list[H.RunSpec]:
    """A reproducible sample of n games. Pure function of (n, seed, swans)."""
    rng = random.Random(seed)
    specs: list[H.RunSpec] = []
    for i in range(n):
        choices = {r: rng.choice(_OPTIONS) for r in range(1, H.N_ROUNDS + 1)}
        invest = rng.choice(INVEST_LEVELS)
        capex = rng.choice(CAPEX_LEVELS)
        pathway = rng.choice(PATHWAYS)
        specs.append(H.RunSpec(
            choices=choices,
            seed=seed * 100_000 + i,
            seed_string=f"stress-{seed}-{i}",
            spend={"invest": {b: invest for b in _BU_IDS},
                   "capex": {b: capex for b in _BU_IDS}},
            session_config={"ending_pathway": pathway},
            ped_overrides=dict(_SWANS_ON if swans else _SWANS_OFF),
            label=f"stress-{seed}-{i}",
        ))
    return specs


def run(spec: H.RunSpec, rules_version: str) -> Outcome:
    """Drive one sampled game and record what the engine graded.

    A run that raises is RECORDED, not swallowed and not fatal: a sweep of two
    thousand games that dies on one pre_tick rejection tells you nothing, and one
    that silently drops it biases the distribution it exists to measure.
    """
    out = Outcome(
        label=spec.label, rules_version=rules_version,
        swans=bool((spec.ped_overrides or {}).get("black_swan_events_enabled")),
        pathway=(spec.session_config or {}).get("ending_pathway", "activist_ultimatum"),
        invest=next(iter((spec.spend or {}).get("invest", {}).values()), 0.0),
        capex=next(iter((spec.spend or {}).get("capex", {}).values()), 0),
    )
    try:
        trace, gs, bus = H.drive(spec=spec, rules_version=rules_version)
    except Exception as exc:                      # noqa: BLE001 — recorded, see above
        out.failed = f"{type(exc).__name__}: {exc}"[:200]
        return out

    aef = _finale(gs)
    out.mr = float(aef.get("regenerative_multiple", 0.0) or 0.0)
    out.terminal_value = float(aef.get("terminal_value", 0.0) or 0.0)
    out.exit_multiple = float(aef.get("exit_multiple_applied", 0.0) or 0.0)
    out.wacc = float(aef.get("exit_multiple_wacc_used", 0.0) or 0.0)
    out.archetype = str(aef.get("archetype", ""))
    out.profile = str(aef.get("profile", ""))
    out.sct = float(aef.get("supply_chain_transparency", 0.0) or 0.0)
    out.sdg_index = float((aef.get("sdg_impact") or {}).get("sdg_index", 0.0) or 0.0)
    out.m_sdg = float(aef.get("sdg_multiplier", 1.0) or 1.0)
    out.treasury = float(gs.get("corporate_treasury", 0.0) or 0.0)
    out.equity_wiped_out = bool(aef.get("equity_wiped_out"))

    breakdown = aef.get("mr_breakdown")
    if isinstance(breakdown, dict):
        out.bonuses = tuple(sorted(k for k, v in breakdown.items()
                                   if isinstance(v, (int, float)) and v and k != "base"))
    # The ENGINE'S OWN pre-clamp value and clamp verdict (round_logic.py:493-494,
    # :3129-3130), not a reconstruction. The first version of this summed
    # mr_breakdown, which over-counts: the pathway calculators put BOTH their
    # components and the pathway_mr_delta total in the same dict, so
    # adaptation_premium + carbon_transition + climate_leader were each counted
    # twice and the clamp looked like it bound in 14% of runs. It does not.
    out.mr_raw = float(aef.get("mr_raw", out.mr) or out.mr)
    out.mr_ceiling_clamped = bool(aef.get("mr_ceiling_clamped"))
    out.mr_floor_clamped = bool(aef.get("mr_floor_clamped"))
    return out


def paired(n: int, seed: int, swans: bool = False) -> list[tuple[Outcome, Outcome]]:
    """The same n games under both rule sets. Pairing is what makes a 1% shift
    visible without an enormous sample."""
    return [(run(spec, "2026.09"), run(spec, "2026.10"))
            for spec in sample_specs(n, seed, swans)]


# ── summary statistics, kept here so the report and the tests agree ─────────

def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = q * (len(ordered) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[int(pos)]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def describe(values: list[float]) -> dict:
    clean = [v for v in values if v is not None]
    if not clean:
        return {"n": 0}
    return {
        "n": len(clean),
        "min": round(min(clean), 4),
        "p05": round(_quantile(clean, 0.05), 4),
        "p50": round(_quantile(clean, 0.50), 4),
        "p95": round(_quantile(clean, 0.95), 4),
        "max": round(max(clean), 4),
        "mean": round(sum(clean) / len(clean), 4),
    }


def relative_delta(before: float, after: float) -> float:
    """Signed relative change, 0.0 when the baseline is 0 (never inf)."""
    if before == 0:
        return 0.0
    return (after - before) / abs(before)
