"""
Muressons — FINANCIAL Golden Round-Trace Oracle
═══════════════════════════════════════════════════════════════════════════
Regression oracle for the money surface: treasury, EBITDA, emissions, synergy,
per-BU revenue/opex/carbon, and the two terminal outputs (M_R, terminal value).

WHY THIS EXISTS
    `test_stakeholder_golden_trace.py` proved the mechanism works and is the
    model for this file. It captures reputation, social licence, governance risk
    and NPC state — and nothing else. Treasury, EBITDA, tCO2e, synergy, M_R and
    terminal valuation, i.e. **the entire financial core, the part students are
    graded on**, had no characterization test at all.

    That is the gap this closes. It does not assert the engine is CORRECT — no
    test can, the model is a judgement call. It asserts the engine is UNCHANGED,
    which is the only property that lets a validated simulation be refactored,
    retuned or de-randomised without silently moving every grade.

WHAT IT DRIVES
    The real pipeline, exactly as commit_turn does it:
        process_tick  →  re-inject stochastic_seed  →  run_new_engines
    with the same carry-forward semantics (process_tick rebuilds global_state
    from a whitelist; run_new_engines mutates the result in place).

SCOPE — MEASURED, NOT ASSUMED
    I first wrote here that this oracle covers org_politics / board_governance /
    supply_chain_network (the three the stakeholder oracle disables because they
    roll on the bare global `random` module, and which are ON in production and
    all move money). Then I instrumented the module and counted.

    A full 10-round run of this script makes **exactly 3** draws on the bare
    global `random` module, all from one post_tick round handler. Those three
    engines never draw here — they are gated on state this script does not
    reach. So the honest position is: this oracle pins the CORE money path
    (process_tick's financial + operational + reporting layers, post_tick's
    per-round impacts, the new-engines batch, and the reporting-truth resync)
    and does NOT yet cover those three engines.

    `test_bare_global_random_draws_stay_pinned` turns that measurement into an
    enforced invariant, in both directions: if a change routes a new money path
    through un-seeded randomness the count rises and the test fails, and when
    remediation #15 converts the twelve bare-`random` sites to `event_rng` the
    count should fall to 0 and the test will say so. Extending the script to
    reach those three engines is worthwhile follow-up work; claiming it already
    does was not.

REBASELINE (deliberate, reviewed)
        MURESSONS_REBASELINE_GOLDEN=1 pytest tests/test_financial_golden_trace.py
    Commit the JSON diff IN THE SAME COMMIT as the change that caused it, so the
    review shows exactly which numbers moved and by how much. A rebaseline with
    no accompanying engine change is a bug report, not a chore.
"""

from __future__ import annotations

import copy
import json
import os
import random
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

from engine import process_tick                                    # noqa: E402
from round_logic import post_tick, run_new_engines                 # noqa: E402
from terminal_valuation import (                                   # noqa: E402
    calculate_mr, calculate_terminal_value, determine_archetype,
)

_GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
_GOLDEN_PATH = _GOLDEN_DIR / "financial_trace.json"
_SEED = 20260802
_ROUND_DP = 4
_N_ROUNDS = 10
# Measured, then pinned — see test_bare_global_random_draws_stay_pinned.
_EXPECTED_BARE_RANDOM_DRAWS = 0  # remediation #15 landed 2026-08-31 (DEEP-4)

# Only the two genuinely out-of-scope engines are disabled: black swans and the
# decision timer add noise without adding financial coverage. Everything that
# moves money stays ON — see the scope note in the module docstring.
_PED_OVERRIDES = {
    "black_swan_events_enabled": False,
    "decision_timer_enabled": False,
}


def _make_initial_global() -> dict:
    return {
        "round_number": 1,
        "corporate_treasury": 50_000_000,
        "group_reputation": 60.0,
        "synergy_multiplier": 0.35,
        "cost_of_capital": 0.05,
        "active_event_flags": {"stochastic_seed": f"fin-golden-{_SEED}"},
        "historical_ebitda": 0,
        "tco2e_emissions": 0,
        "green_transition_fund": 0,
        "tipping_point_active": False,
        "workforce_readiness": 50.0,
        "momentum_history": [],
        "pending_capex_projects": [],
    }


def _make_initial_bus() -> list[dict]:
    configs = {
        "pharma":         {"revenue_base": 20_000_000, "opex_base": 12_000_000, "carbon_intensity": 35},
        "electronics":    {"revenue_base": 18_000_000, "opex_base": 11_000_000, "carbon_intensity": 55},
        "consumer_goods": {"revenue_base": 15_000_000, "opex_base":  9_000_000, "carbon_intensity": 40},
        "software":       {"revenue_base": 22_000_000, "opex_base":  8_000_000, "carbon_intensity": 15},
    }
    return [
        {
            "bu_id": bu_id,
            "revenue_base": cfg["revenue_base"],
            "opex_base": cfg["opex_base"],
            "reputation_score": 60.0,
            "social_license_score": 55.0,
            "governance_risk_score": 20.0,
            "natural_capital_debt": 50.0,
            "carbon_intensity": cfg["carbon_intensity"],
            "water_dependency": 30.0,
            "staff_burnout_index": 15.0,
            "risk_factors": {"top_investment_streak": 0},
            "consecutive_zero_rounds": 0,
        }
        for bu_id, cfg in configs.items()
    ]


# A script that deliberately spans the spending range: one BU starved, one
# heavily funded, two mid — so the CSF/CAPEX/loan-interest branches all fire.
_CHOICE_BY_ROUND = {
    1: "option_b", 2: "option_a", 3: "option_c", 4: "option_a", 5: "option_b",
    6: "option_c", 7: "option_a", 8: "option_b", 9: "option_c", 10: "option_a",
}
_INVEST_BY_BU = {"pharma": 0.9, "electronics": 0.7, "consumer_goods": 0.5, "software": 0.3}
_CAPEX_BY_BU = {"pharma": 500_000, "electronics": 0, "consumer_goods": 250_000, "software": 100_000}
# Crisis severity is fixed rather than swept: production derives it from the
# round config (TECH-1 — the client value is ignored), so a constant here keeps
# the oracle about the money path rather than about crisis calibration.
_CRISIS_SEVERITY = 20.0

# CALIBRATION NOTE, recorded because building this oracle surfaced it.
# The parameters above were not chosen for realism; they were chosen because
# they keep the run SOLVENT. In this harness the solvency band is narrow: a
# balanced 0.3-investment run with 1M capex per BU per round is insolvent by
# round 4 and reaches -484M by round 10. Several plausible scripts die by R5.
# A golden that spends six of its ten rounds in a deep-insolvency regime pins
# mostly clamp behaviour, so this script deliberately stays in the normal
# operating band where regressions actually matter.
#   Caveat before drawing conclusions about difficulty: this harness omits
#   pre_tick and the router's pillar aggregation, and holds crisis severity
#   constant, so it is NOT a calibration measurement. It is, however, a cheap
#   and now-reproducible way to take one — see the dry-run pre-flight (§8.1
#   Phase B), which is the tool actually built for that question.


def _decisions_for_round(rnd: int, bus: list[dict]) -> list[dict]:
    choice = _CHOICE_BY_ROUND.get(rnd, "option_b")
    return [
        {
            "bu_id": bu["bu_id"],
            "investment_ratio": _INVEST_BY_BU.get(bu["bu_id"], 0.3),
            "capex_allocated": _CAPEX_BY_BU.get(bu["bu_id"], 1_000_000),
            "choice_selected": choice,
        }
        for bu in bus
    ]


def _r(x):
    return round(float(x), _ROUND_DP) if isinstance(x, (int, float)) else x


# The money surface. Anything added here must also be rebaselined.
_GLOBAL_KEYS = (
    "corporate_treasury", "historical_ebitda", "tco2e_emissions",
    "synergy_multiplier", "cost_of_capital", "avg_carbon_intensity",
    "total_ncd", "green_transition_fund", "avg_social_license",
)
_BU_KEYS = ("revenue_base", "opex_base", "carbon_intensity", "natural_capital_debt")


def _snapshot(rnd: int, gs: dict, bus: list[dict]) -> dict:
    return {
        "round": rnd,
        "global": {k: _r(gs.get(k, 0) or 0) for k in _GLOBAL_KEYS},
        # Sorted by bu_id so a change in backend row ordering can never move a
        # number here. (Production DOES differ: Postgres returns BUs ordered by
        # bu_id, the memory store returns creation order, and the engine indexes
        # into that list positionally — remediation #18.)
        "bus": [
            {"bu_id": bu["bu_id"], **{k: _r(bu.get(k, 0) or 0) for k in _BU_KEYS}}
            for bu in sorted(bus, key=lambda b: b["bu_id"])
        ],
    }


def _terminal_snapshot(gs: dict, bus: list[dict]) -> dict:
    """The two numbers a student is actually graded on."""
    flags = gs.get("active_event_flags") or {}
    avg_slo = sum(float(b.get("social_license_score", 0) or 0) for b in bus) / max(len(bus), 1)
    avg_burnout = sum(float(b.get("staff_burnout_index", 0) or 0) for b in bus) / max(len(bus), 1)
    mr_result = calculate_mr(
        flags=flags,
        avg_slo=avg_slo,
        avg_burnout=avg_burnout,
        workforce_readiness=float(gs.get("workforce_readiness", 50) or 50),
        synergy_multiplier=float(gs.get("synergy_multiplier", 1.0) or 1.0),
    )
    mr = mr_result["mr"] if isinstance(mr_result, dict) and "mr" in mr_result else mr_result
    tv = calculate_terminal_value(bus, mr if isinstance(mr, (int, float)) else 1.0)
    archetype = determine_archetype(mr if isinstance(mr, (int, float)) else 1.0)
    return {
        "m_r": _r(mr) if isinstance(mr, (int, float)) else mr,
        "terminal_valuation": _r(tv["terminal_value"]) if isinstance(tv, dict) and "terminal_value" in tv else _r(tv),
        "archetype": archetype.get("key") if isinstance(archetype, dict) else archetype,
    }


def _reporting_truth_resync(new_global: dict, new_bus: list[dict]) -> None:
    """Replicate router.py's REPORTING-TRUTH RESYNC, verbatim.

    THIS IS NOT COSMETIC, and building this oracle is how we found out.
    process_tick derives historical_ebitda / tco2e_emissions inside its
    financial layer, and the BU table then keeps mutating — operational layer,
    reporting layer, pillar aggregation, post_tick, the new-engines batch. The
    router recomputes both from the FINAL BU table before persisting, so
    `historical_ebitda` in stored state is a SNAPSHOT (sum of revenue - opex),
    not a running total.

    Without this step the engine's mid-pipeline value persists and feeds the
    next round, and it compounds: a 10-round run with ZERO capex reached an
    EBITDA of -26,141,599,849 against a group revenue of ~75M. That number is
    an artefact of the harness, not the engine — but it is exactly the kind of
    artefact that would have been baked into a golden and defended for months.

    Keep this function byte-identical to router.py:2583-2590.
    """
    new_global["historical_ebitda"] = round(
        sum((bu.get("revenue_base") or 0) - (bu.get("opex_base") or 0) for bu in new_bus), 2
    )
    new_global["tco2e_emissions"] = round(
        sum((bu.get("carbon_intensity") or 0) * (bu.get("revenue_base") or 0) / 1_000_000 for bu in new_bus), 1
    )
    for bu in new_bus:
        bu["absolute_emissions"] = round(
            (bu.get("carbon_intensity") or 0) * (bu.get("revenue_base") or 0) / 1_000_000, 2
        )


def generate_trace(ped_overrides: dict | None = None, seed_global_rng: bool = True) -> list[dict]:
    """Run the fixed, seeded 10-round simulation and return the snapshot list.

    `seed_global_rng=False` is used by the reproducibility acceptance test: with
    the twelve bare-`random` engine sites converted to `event_rng` (#15), the
    cohort seed alone will be sufficient and this argument becomes moot.
    """
    if seed_global_rng:
        random.seed(_SEED)

    overrides = dict(_PED_OVERRIDES if ped_overrides is None else ped_overrides)
    gs = _make_initial_global()
    bus = _make_initial_bus()
    previous_flags: dict = dict(gs["active_event_flags"])
    trace: list[dict] = []

    for rnd in range(1, _N_ROUNDS + 1):
        gs["round_number"] = rnd
        gs["pedagogical_overrides"] = dict(overrides)
        decisions = _decisions_for_round(rnd, bus)

        result = process_tick(
            current_global=copy.deepcopy(gs),
            current_bus=copy.deepcopy(bus),
            decisions=decisions,
            dividends_paid=500_000 if rnd > 1 else 0,
            crisis_severity=_CRISIS_SEVERITY,
            imitation_decay_rate=0.10,
            decision_paradigm="legacy_abc",
        )
        new_global, new_bus, events = result["global_state"], result["bu_states"], result["events"]

        # process_tick rebuilds active_event_flags from `events` and drops the
        # seed; production re-merges persistent flags in the router. Re-inject so
        # round 2+ event_rng streams stay deterministic.
        new_global.setdefault("active_event_flags", {})["stochastic_seed"] = f"fin-golden-{_SEED}"
        new_global["pedagogical_overrides"] = dict(overrides)

        # ── post_tick, then run_new_engines: production's order ──────────────
        # The stakeholder oracle skips post_tick because it only captures
        # reputation/SLO. For MONEY that would be a large hole: post_tick is
        # where the case table's per-round treasury and revenue impacts land, so
        # a trace without it would pin a state production never produces.
        try:
            post_tick(round_number=rnd, global_state=new_global, bu_states=new_bus,
                      decisions=decisions, events=events,
                      previous_flags=previous_flags, decision_paradigm="legacy_abc")
        except Exception as exc:
            trace.append({"round": rnd, "error": f"post_tick raised: {exc}"})
            break

        try:
            run_new_engines(round_number=rnd, global_state=new_global,
                            bu_states=new_bus, events=events)
        except Exception as exc:
            trace.append({"round": rnd, "error": f"run_new_engines raised: {exc}"})
            break

        _reporting_truth_resync(new_global, new_bus)

        trace.append(_snapshot(rnd, new_global, new_bus))
        previous_flags = dict(new_global.get("active_event_flags") or {})
        gs, bus = new_global, new_bus

    trace.append({"terminal": _terminal_snapshot(gs, bus)})
    return trace


def _load_golden():
    if not _GOLDEN_PATH.exists():
        return None
    return json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))


def _write_golden(trace) -> None:
    _GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    _GOLDEN_PATH.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _first_diff(golden, current) -> str:
    if len(golden) != len(current):
        return f"entry count differs: golden={len(golden)} current={len(current)}"
    for g, c in zip(golden, current):
        if g != c:
            return (f"first difference at {g.get('round', 'terminal')}:\n"
                    f"  golden : {json.dumps(g, sort_keys=True)}\n"
                    f"  current: {json.dumps(c, sort_keys=True)}")
    return "no structural diff (unexpected)"


# ═══════════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════════

def test_trace_is_deterministic():
    """Same seed, same script, twice in one process → identical.

    If THIS fails, an un-seeded source of randomness is in the money path and
    nothing below can be trusted. Fix that before reading the golden diff.
    """
    assert generate_trace() == generate_trace(), "financial trace is not deterministic"


def test_golden_trace_matches():
    """The money surface must equal the committed golden."""
    current = generate_trace()
    if os.getenv("MURESSONS_REBASELINE_GOLDEN") == "1":
        _write_golden(current)
        pytest.skip("financial golden rebaselined — review and commit the JSON diff")
    golden = _load_golden()
    assert golden is not None, (
        f"{_GOLDEN_PATH} is missing. Create it with "
        "MURESSONS_REBASELINE_GOLDEN=1 pytest tests/test_financial_golden_trace.py"
    )
    assert golden == current, (
        "FINANCIAL TRACE CHANGED — treasury / EBITDA / emissions / synergy / M_R / "
        "terminal value are not what the golden records.\n\n"
        + _first_diff(golden, current)
        + "\n\nIf this change was deliberate, rebaseline with "
          "MURESSONS_REBASELINE_GOLDEN=1 and commit the JSON diff in the same commit."
    )


def test_the_graded_numbers_are_actually_captured():
    """Guard against a future edit quietly narrowing the capture surface.

    The stakeholder oracle is green and always has been — because it never
    looked at the money. That failure mode is invisible unless something asserts
    the surface itself.
    """
    trace = generate_trace()
    rounds = [e for e in trace if "round" in e]
    assert len(rounds) == _N_ROUNDS
    for key in ("corporate_treasury", "historical_ebitda", "tco2e_emissions", "synergy_multiplier"):
        assert key in rounds[-1]["global"], f"{key} dropped out of the capture surface"
    terminal = trace[-1]["terminal"]
    for key in ("m_r", "terminal_valuation", "archetype"):
        assert key in terminal, f"{key} dropped out of the terminal capture"
    assert isinstance(terminal["terminal_valuation"], (int, float))


def test_treasury_actually_moves_across_the_run():
    """A trace of ten identical numbers would pass every assertion above while
    pinning nothing. Confirm the script exercises the engine."""
    treasuries = [e["global"]["corporate_treasury"] for e in generate_trace() if "round" in e]
    assert len(set(treasuries)) > 1, "treasury never moved — the script is not exercising the engine"


def test_bare_global_random_draws_stay_pinned():
    """The money path makes ZERO un-seeded random draws — hold it there.

    Remediation #15 landed (DEEP-4, 2026-08-31): the last three bare draws —
    impact_engine's R5 cyclone/NBS and R9 strike/retraining rolls — moved onto
    rng_util's named per-cohort streams (test_seeded_stochastics.py pins the
    reproducibility contract). This counter stays as the tripwire: ANY count
    above zero means someone routed a new money path through the bare global
    `random` module, which interleaves across concurrent commits and cannot be
    replayed from a cohort seed. The treasury-waterfall runner's strict xfail
    remains — a residual entropy source outside the money path still varies
    across processes.
    """
    import random as _random
    seen = []
    originals = {n: getattr(_random, n)
                 for n in ("random", "randint", "uniform", "choice", "sample", "gauss", "shuffle")}
    try:
        for name, orig in originals.items():
            def _wrap(o=orig):
                def w(*a, **k):
                    seen.append(1)
                    return o(*a, **k)
                return w
            setattr(_random, name, _wrap())
        generate_trace()
    finally:
        for name, orig in originals.items():
            setattr(_random, name, orig)

    assert len(seen) == _EXPECTED_BARE_RANDOM_DRAWS, (
        f"bare global random draws in the money path changed: "
        f"{len(seen)} (was {_EXPECTED_BARE_RANDOM_DRAWS}).\n"
        "  MORE  -> a money path now depends on un-seeded randomness; it cannot be "
        "replayed from a cohort seed.\n"
        "  FEWER -> good. If it is 0, remediation #15 has landed: delete this test "
        "and assert reproducibility from the cohort seed alone instead."
    )


def test_the_seed_actually_changes_the_outcome():
    """A golden pinned to a seed that does nothing would be a golden pinned to
    nothing. Changing the cohort seed must move the trace."""
    import test_financial_golden_trace as _self
    original = _self._SEED
    try:
        baseline = generate_trace()
        _self._SEED = original + 1
        assert generate_trace() != baseline, (
            "changing the cohort stochastic_seed did not change the trace — the "
            "seeded event_rng streams are not reaching the captured surface"
        )
    finally:
        _self._SEED = original


if __name__ == "__main__":  # regenerate: python tests/test_financial_golden_trace.py
    _write_golden(generate_trace())
    print(f"wrote {_GOLDEN_PATH}")
