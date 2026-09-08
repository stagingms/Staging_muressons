"""Muressons — option-matrix golden harness (no tests in this module).

WHY THIS EXISTS
    tests/test_financial_golden_trace.py and tests/test_stakeholder_golden_trace.py
    are good characterization oracles and this module does not replace them. They
    share one limitation that matters for any work on the flag layer: both drive a
    SINGLE fixed option path. _CHOICE_BY_ROUND touches 10 of the 30 (round, option)
    pairs that round_configs declares, so two thirds of the decision surface — and
    23 of the 33 round flags — are exercised by no fixture at all.

    The consequence is concrete. Reviving a flag set by an option the golden path
    never takes moves no fixture, so the change ships green. This module closes
    that hole by driving a covering set of paths instead of one.

WHAT IT DRIVES — the production sequence, in production's order
        pre_tick                           (router.py:2906)
          crisis severity from the SERVER   (router.py:2894, F-07)
        attach the option's flags_set       (router.py:2946-2960, FLAG-3)
        stamp difficulty_tier               (router.py:2963)
        stamp the _systemic_toggles bag     (router.py:2977-2988, IMP-06)
        process_tick                        (router.py:3003)
        merge pre_events into events        (router.py:3036)
        re-inject stochastic_seed          (process_tick drops it; router re-merges)
        _forward_persistent_flags           (router.py:3121, F-04)
        post_tick                           (router.py:3126)
        run_new_engines                     (router.py:3170)
        reporting-truth resync              (router.py:3268)
        three-way active_event_flags merge  (router.py:3322-3325)

    THE MERGE IS THE STEP THE EXISTING ORACLES OMIT. Production merges history ->
    post_tick flags -> events, which is what keeps r1_flags..r10_flags alive to the
    finale. Without it only the current round's list survives: measured, 4 flags
    visible at R10 instead of 17.

WHY THE OTHER FOUR STEPS ARE HERE (Phase 3, 2026-09-08)
    Phase 0 shipped this harness with pre_tick, the flags_set attach and the
    session-config stamps deliberately omitted, and said so. Phase 3's read probe
    made the omissions load-bearing, because a consumer the harness never executes
    is indistinguishable from a consumer that cannot fire — which is the exact
    distinction the probe exists to make. Measured, each omission hid a documented
    consumer:

      pre_tick          round_logic._pre_r4_contagion is the ONLY reader of
                        electronics_blindspot and deferred_audit. Without pre_tick
                        both look dead. With it, R4 crisis severity moves 40 -> 80
                        (blindspot) or -> 60 (deferred audit) and the pre_events
                        land in the flag namespace via router.py:3036.

      server crisis     F-07 made crisis severity server-derived: 0 in every round
                        but R4, where round_configs supplies 40. The harness held
                        20.0 in all ten rounds, a value production never passes.

      flags_set attach  Measured on all_c with the attach absent:
                        apply_decision_sentiment moved 0 stakeholders in all ten
                        rounds. With it: carbon_deferred moves 1 at R3,
                        deny_and_deflect moves 2 at R4, quiet_patch moves 2 at R6.
                        Those three are Appendix B's "LIVE (sentiment only)" flags,
                        and without the attach this harness reproduced inside the
                        test suite the very bug FLAG-3 fixed in production.

      session config    difficulty_tier gates the covenant ratio; the
                        _systemic_toggles bag is what systemic_risk_engine reads to
                        decide whether the systemic engines run at all. The bag is
                        built as the router builds it — a cohort's
                        pedagogical_overrides win over the settings default — so
                        PED_OVERRIDES still holds black swans off.

    The score surface gained a `sentiment` block for the same reason: a flag whose
    only effect is on stakeholder attitudes moved nothing this harness recorded.

TERMINAL COMPUTATION
    The finale reads flags through flag_utils.mr_flags_from (the F-15/WP-14 fix),
    NOT through the raw active_event_flags dict. Passing the raw dict lets
    calculate_mr see ~130 event keys as if they were flags while missing every
    option flag, because option flags live inside rN_flags lists. This harness uses
    the production path and pins the divergence.

SCOPE — MEASURED, NOT ASSUMED
    Black swans and the decision timer are disabled, as in the financial oracle,
    so the matrix stays about decisions rather than draws. The router's pillar
    aggregation is NOT driven; this is the legacy_abc paradigm only. Extending to
    pillar mode is follow-up work and is named as such rather than implied.

REBASELINE (deliberate, reviewed)
        MURESSONS_REBASELINE_MATRIX=1 pytest tests/test_option_matrix_golden.py
    Commit the JSON diff in the SAME commit as the change that caused it. A
    rebaseline with no accompanying engine change is a bug report, not a chore.
"""

from __future__ import annotations

import copy
import json
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

from engine import process_tick                                    # noqa: E402
from round_logic import (                                          # noqa: E402
    base_crisis_severity_for_round, post_tick, pre_tick, run_new_engines,
    _fetch_options_for_industry as _fetch_options,
    _get_primary_choice as _primary_choice,
)
from round_configs import get_round_config                         # noqa: E402
from flag_utils import collect_all_flags, mr_flags_from            # noqa: E402
from rules import (                                                # noqa: E402
    DEFAULT_RULES_VERSION, RULES_FLAG,
)
from systemic_risk_engine import (                                 # noqa: E402
    SYSTEMIC_RISK_TOGGLE_KEYS, SYSTEMIC_TOGGLES_FLAG,
)
from terminal_valuation import (                                   # noqa: E402
    calculate_mr, calculate_terminal_value, determine_archetype,
)

GOLDEN_DIR = Path(__file__).resolve().parent / "golden" / "matrix"
# One fixture set per rule set. The baseline directory keeps its name so the
# Phase 0-3 fixtures are not silently renamed out from under their history.
GOLDEN_DIRS = {
    "2026.09": GOLDEN_DIR,
    "2026.10": GOLDEN_DIR.parent / "matrix_2026_10",
}
N_ROUNDS = 10
ROUND_DP = 4

# Black swans and the decision timer add noise without adding decision coverage.
# Everything that moves money stays ON.
PED_OVERRIDES = {
    "black_swan_events_enabled": False,
    "decision_timer_enabled": False,
}

# The session-level difficulty the router stamps at router.py:2963. "advanced" is
# database_memory.create_session's default, so this is the production value for a
# cohort whose facilitator changed nothing.
DIFFICULTY_TIER = "advanced"

# router.py:2384-2392 — the keys _forward_persistent_flags carries from the stored
# flags into the post-tick state. Copied here rather than imported because router
# pulls in FastAPI and the database layer; test_option_matrix_golden asserts the
# two tuples are identical, so a change there fails here rather than drifting.
PERSISTENT_FLAG_KEYS = (
    "stochastic_seed", "loan_interest_rate", "ending_pathway", "difficulty_tier",
    "industry_vertical", "region_id", SYSTEMIC_TOGGLES_FLAG, RULES_FLAG,
)

# ── the covering set ────────────────────────────────────────────────────────
# Three uniform paths cover all 30 (round, option) pairs. `legacy_mixed` is the
# existing financial oracle's path, carried so this harness can be proved a
# faithful superset of it rather than a different engine.
PATHS: dict[str, dict[int, str]] = {
    "all_a":        {r: "option_a" for r in range(1, N_ROUNDS + 1)},
    "all_b":        {r: "option_b" for r in range(1, N_ROUNDS + 1)},
    "all_c":        {r: "option_c" for r in range(1, N_ROUNDS + 1)},
    "legacy_mixed": {1: "option_b", 2: "option_a", 3: "option_c", 4: "option_a", 5: "option_b",
                     6: "option_c", 7: "option_a", 8: "option_b", 9: "option_c", 10: "option_a"},
    # A DIRECTED CASE, not a coverage path: the four above already cover 30/30
    # (round, option) pairs. distress_c exists because Phase 3's server-derived
    # crisis severity moved all_c out of insolvency (final treasury -19,379,984 ->
    # +29,611,117) and with it went the whole distress cascade the fixtures used
    # to pin: survival_mode, cfo_austerity_active, dividends_clamped,
    # dividend_ratchet_triggered, distress_detected and phase_transition, all of
    # which appeared only on all_c at R9-R10. Keeping the four decision paths in
    # the normal operating band is right — the financial oracle's calibration note
    # argues it — but the cascade still has to be covered by something. This path
    # takes all_c's options on the spend profile that oracle note measured as
    # insolvent by round 4 (0.3 investment, $1M capex per BU per round), and
    # test_the_distress_cascade_stays_covered holds all six flags here.
    "distress_c":   {r: "option_c" for r in range(1, N_ROUNDS + 1)},
    # TWO MORE DIRECTED CASES, for the dimension the option matrix cannot span.
    # The ending pathway is session configuration (round_logic.py:721, :2653 read
    # it off the flags; it is one of router._PERSISTENT_FLAG_KEYS), not a decision
    # — so four of the five M_R pathway calculators run for NO path unless a path
    # is configured onto them, and the flags they read look dead for a reason that
    # has nothing to do with the flags.
    #   adaptation  climate_black_swan, and the only path taking R3 option_a
    #               (early_decarboniser) WITH R5 option_b (nature_based_resilience)
    #               — Appendix B §B.14.1's Adaptation Premium needs both, and the
    #               three uniform paths can never hold both at once.
    #   regulatory  regulatory_shutdown, where scope_3_transparency earns the
    #               +0.20 Supply Chain Transparency premium (ending_pathways.py:755).
    "adaptation":   {1: "option_b", 2: "option_b", 3: "option_a", 4: "option_b", 5: "option_b",
                     6: "option_b", 7: "option_b", 8: "option_b", 9: "option_b", 10: "option_b"},
    "regulatory":   {1: "option_b", 2: "option_a", 3: "option_a", 4: "option_a", 5: "option_b",
                     6: "option_b", 7: "option_b", 8: "option_b", 9: "option_b", 10: "option_b"},
}

# Session-level configuration per path — the keys the router stamps at session
# creation and _forward_persistent_flags carries forward. Absent means the
# platform default, which for ending_pathway is "activist_ultimatum"
# (round_logic.py:721).
SESSION_CONFIG: dict[str, dict] = {
    "adaptation": {"ending_pathway": "climate_black_swan"},
    "regulatory": {"ending_pathway": "regulatory_shutdown"},
}

# Per-path spend. Absent from this map means the default profile below, which the
# financial oracle also uses; distress_c is the only path that overrides it.
SPEND: dict[str, dict] = {
    "distress_c": {
        "invest": {"pharma": 0.3, "electronics": 0.3, "consumer_goods": 0.3, "software": 0.3},
        "capex":  {"pharma": 1_000_000, "electronics": 1_000_000,
                   "consumer_goods": 1_000_000, "software": 1_000_000},
    },
}
# Per-path seeds are fixed so paths differ from each other but never from
# themselves. legacy_mixed reuses the financial oracle's seed so the money
# surface is comparable.
SEEDS: dict[str, int] = {
    "all_a": 20260901, "all_b": 20260902, "all_c": 20260903, "legacy_mixed": 20260802,
    "distress_c": 20260904, "adaptation": 20260905, "regulatory": 20260906,
}
# The stochastic_seed STRING is what drives event_rng, not the int. legacy_mixed
# reuses the financial oracle's exact string so its money surface is directly
# comparable with tests/golden/financial_trace.json; changing it silently would
# make the fidelity test meaningless while still passing.
SEED_STRINGS: dict[str, str] = {
    "all_a": "matrix-golden-20260901",
    "all_b": "matrix-golden-20260902",
    "all_c": "matrix-golden-20260903",
    "legacy_mixed": "fin-golden-20260802",
    "distress_c": "matrix-golden-20260904",
    "adaptation": "matrix-golden-20260905",
    "regulatory": "matrix-golden-20260906",
}

_INVEST_BY_BU = {"pharma": 0.9, "electronics": 0.7, "consumer_goods": 0.5, "software": 0.3}
_CAPEX_BY_BU = {"pharma": 500_000, "electronics": 0, "consumer_goods": 250_000, "software": 100_000}

# The flat crisis severity the financial oracle holds (test_financial_golden_trace
# _CRISIS_SEVERITY). Production derives severity per round instead (F-07), so this
# value is used ONLY by drive(production_steps=False) — the oracle-compatibility
# mode that exists to prove this harness is the oracle's driver plus named steps
# rather than a different engine. Nothing in the matrix uses it.
_ORACLE_CRISIS_SEVERITY = 20.0


def make_initial_global(seed: int, seed_string: str | None = None) -> dict:
    return {
        "round_number": 1,
        "corporate_treasury": 50_000_000,
        "group_reputation": 60.0,
        "synergy_multiplier": 0.35,
        "cost_of_capital": 0.05,
        "active_event_flags": {"stochastic_seed": seed_string or f"matrix-golden-{seed}"},
        "historical_ebitda": 0,
        "tco2e_emissions": 0,
        "green_transition_fund": 0,
        "tipping_point_active": False,
        "workforce_readiness": 50.0,
        "momentum_history": [],
        "pending_capex_projects": [],
    }


def make_initial_bus() -> list[dict]:
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


def declared_round_options() -> set[tuple[int, str]]:
    """Every (round, option) pair round_configs declares. The coverage ratchet
    compares the matrix against this, so adding an option fails the suite until
    the matrix covers it."""
    pairs = set()
    for rnd in range(1, N_ROUNDS + 1):
        for opt in (get_round_config(rnd).get("options") or {}):
            pairs.add((rnd, opt))
    return pairs


def option_flags_for(rnd: int, choice: str, bus: list[dict]) -> list[str]:
    """The flags_set the router attaches to the decision (router.py:2953-2957)."""
    try:
        opts = _fetch_options(rnd, bus, decision_paradigm="legacy_abc")
        return list((opts.get(choice) or {}).get("flags_set", []) or [])
    except Exception:
        return []


def _r(x):
    return round(float(x), ROUND_DP) if isinstance(x, (int, float)) else x


@dataclass(frozen=True)
class RunSpec:
    """One drivable game, given explicitly rather than looked up by name.

    The named paths in PATHS are the covering array and the directed cases: a
    fixed, reviewed set whose fixtures are committed. The stress harness needs
    THOUSANDS of runs that are none of those things, and it must drive them
    through the same `drive` loop — a stress harness with its own copy of the
    production sequence would measure a different engine from the one the
    fixtures pin, which is the mistake Phase 3 spent a day undoing.
    """
    choices: dict            # {round: option_key}
    seed: int
    seed_string: str
    spend: dict | None = None            # {"invest": {...}, "capex": {...}}
    session_config: dict | None = None   # ending_pathway, etc.
    # The cohort toggles. None means PED_OVERRIDES — black swans and the decision
    # timer off, which is what every committed fixture is captured under. The
    # stress harness overrides it to sample the swan-on regime as well, because a
    # threshold re-derived from a swan-free distribution would describe a game
    # nobody plays.
    ped_overrides: dict | None = None
    label: str = "adhoc"


def _spec_for(path_name: str) -> RunSpec:
    """The named paths, expressed as specs, so `drive` has ONE lookup path."""
    return RunSpec(
        choices=PATHS[path_name], seed=SEEDS[path_name],
        seed_string=SEED_STRINGS[path_name], spend=SPEND.get(path_name),
        session_config=SESSION_CONFIG.get(path_name), label=path_name,
    )


def _decisions(rnd: int, bus: list[dict], spec: RunSpec) -> list[dict]:
    choice = spec.choices.get(rnd, "option_b")
    spend = spec.spend or {}
    invest = spend.get("invest", _INVEST_BY_BU)
    capex = spend.get("capex", _CAPEX_BY_BU)
    return [
        {
            "bu_id": bu["bu_id"],
            "investment_ratio": invest.get(bu["bu_id"], 0.3),
            "capex_allocated": capex.get(bu["bu_id"], 1_000_000),
            "choice_selected": choice,
        }
        for bu in bus
    ]


# The money surface, identical to the financial oracle's so the two are comparable.
_GLOBAL_KEYS = (
    "corporate_treasury", "historical_ebitda", "tco2e_emissions",
    "synergy_multiplier", "cost_of_capital", "avg_carbon_intensity",
    "total_ncd", "green_transition_fund", "avg_social_license",
)
_BU_KEYS = ("revenue_base", "opex_base", "carbon_intensity", "natural_capital_debt")
# The score surface — the quantities the flag remediation is expected to move.
_SCORE_KEYS = ("supply_chain_transparency", "workforce_readiness", "group_reputation")


def _systemic_toggle_bag(overrides: dict | None = None) -> dict:
    """router.py:2977-2986. A cohort's pedagogical_overrides win over the settings
    default, which is True."""
    src = PED_OVERRIDES if overrides is None else overrides
    return {k: bool(src.get(k, True)) for k in SYSTEMIC_RISK_TOGGLE_KEYS}


def _forward_persistent_flags(current_global: dict, new_global: dict) -> None:
    """router.py:2384-2392, byte-for-byte. Copies the session-level keys from the
    STORED flags into the post-tick state without overriding what the tick made."""
    stored = current_global.get("active_event_flags") or {}
    target = new_global.setdefault("active_event_flags", {})
    for key in PERSISTENT_FLAG_KEYS:
        value = stored.get(key)
        if value not in (None, "") and key not in target:
            target[key] = value


def _reporting_truth_resync(new_global: dict, new_bus: list[dict]) -> None:
    """router.py's reporting-truth resync. Keep byte-identical to the financial
    oracle's copy, which is in turn kept identical to the router."""
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


def _sentiment_surface(aef: dict) -> dict:
    """Stakeholder attitudes, which engine.py:4802 writes into the events bag and
    the router merges into active_event_flags. Recorded because three of Appendix
    B's LIVE flags — carbon_deferred, deny_and_deflect, quiet_patch — move nothing
    else: their whole effect is the 58-rule sentiment map."""
    rows = aef.get("sentiment_stakeholders") or []
    if not isinstance(rows, list):
        return {}
    return {
        str(s.get("id")): _r(s.get("attitude_score", 0) or 0)
        for s in rows if isinstance(s, dict) and s.get("id")
    }


def _sdg_index(aef: dict) -> float:
    """The SDG Impact Report's aggregate. Recorded because the Phase 4 revival of
    _SDG_FLAG_BONUSES (engine.py:2121) moves NOTHING ELSE this harness captures:
    sdg_index is a report, not a graded number — M_SDG comes from the Corporate
    SDG side track's separate sdg_impact_score — so without this key the probe
    could not tell the revival from no revival."""
    report = aef.get("sdg_impact")
    if not isinstance(report, dict):
        return 0.0
    return _r(report.get("sdg_index", 0.0) or 0.0)


def _escalations(aef: dict) -> dict:
    """WHICH NPC and agent escalations fired, not just what they cost.

    Added after Phase 4 measured the transparency revival's cascade: on all_c the
    revived rules take an autonomous-agent event of -8,374,695 at R6 where the
    baseline takes an NPC enforcement fine of -6,844,448. The MONEY was already
    pinned — treasury and opex_base are in the recorded surface — but the IDENTITY
    of the escalation was not, so a change that swapped one escalation for another
    of similar cost would have moved no fixture at all.

    Identifiers only, never the narrative text: npc_id/action and agent_id/stage
    are stable, while `message`, `label` and `demand` are prose that would churn
    the fixtures on every copy edit.
    """
    npc = (aef.get("npc_stakeholders") or {}).get("npc_actions") or []
    agents = aef.get("agent_summary") or []
    moves = aef.get("_treasury_moves") or []
    return {
        "npc": sorted(f"{a.get('npc_id')}:{a.get('action')}"
                      for a in npc if isinstance(a, dict)),
        "agents": sorted(f"{a.get('agent_id')}:{a.get('stage')}"
                         for a in agents if isinstance(a, dict)),
        "treasury_moves": sorted(
            [str(m.get("engine")), _r(m.get("delta", 0) or 0)]
            for m in moves if isinstance(m, dict)),
    }


def _snapshot(rnd: int, gs: dict, bus: list[dict]) -> dict:
    aef = gs.get("active_event_flags") or {}
    return {
        "round": rnd,
        "global": {k: _r(gs.get(k, 0) or 0) for k in _GLOBAL_KEYS},
        "score": {k: _r(aef.get(k, gs.get(k, 0)) or 0) for k in _SCORE_KEYS},
        "sdg_index": _sdg_index(aef),
        "escalations": _escalations(aef),
        "sentiment": _sentiment_surface(aef),
        # The canonical reader, so the fixture records what a correct consumer
        # would see rather than what the raw dict happens to hold.
        "flags": sorted(collect_all_flags(aef)),
        "bus": [
            {"bu_id": bu["bu_id"], **{k: _r(bu.get(k, 0) or 0) for k in _BU_KEYS}}
            for bu in sorted(bus, key=lambda b: b["bu_id"])
        ],
    }


# The finale's own stamps. round_logic._stamp_finale_valuation writes these onto
# active_event_flags and restamp_finale_valuation re-runs them on the closing
# state; they are the numbers a team is graded on. Phase 0 could not record them
# because it discarded post_tick's return value, so the fixtures pinned
# terminal_snapshot's reconstruction instead — which uses the FIXED exit multiple
# and passes neither hr_investment_rounds nor pathway_bonuses. Measured, that
# reconstruction was wrong: on all_c M_R 1.07 against the engine's 0.92, and on
# distress_c it graded a fragile_giant where the engine graded a stranded_relic.
_FINALE_KEYS = (
    "regenerative_multiple", "terminal_value", "terminal_ebitda",
    "exit_multiple_applied", "exit_multiple_wacc_used", "archetype", "profile",
    "equity_value", "price_per_share", "equity_wiped_out", "net_debt",
)
# Pathway and premium markers the finale sets. Recorded by NAME rather than value
# because they are booleans and floats whose presence is the finding.
_FINALE_MARKERS = (
    "mr_adaptation_premium", "mr_climate_leader_bonus", "mr_carbon_transition_bonus",
    "mr_stranded_asset_penalty", "pathway_config_loaded", "ncd_forgiveness_materiality_bonus",
    "hard_engineering_pulse_reverted", "scandal_shock_prevented",
    "mr_supply_chain_transparency", "mr_proactive_compliance", "exit_multiple_ci_haircut",
)


def finale_snapshot(gs: dict) -> dict:
    """What the engine's own R10 finale stamped, as opposed to what this module
    can reconstruct from the closing state."""
    aef = gs.get("active_event_flags") or {}
    out = {k: _r(aef[k]) for k in _FINALE_KEYS if k in aef}
    marks = sorted(k for k in _FINALE_MARKERS if aef.get(k))
    if marks:
        out["markers"] = marks
    breakdown = aef.get("mr_breakdown")
    if isinstance(breakdown, dict):
        out["mr_breakdown"] = {k: _r(v) for k, v in sorted(breakdown.items())
                               if isinstance(v, (int, float))}
    return out


def terminal_snapshot(gs: dict, bus: list[dict], production_path: bool = True) -> dict:
    """The graded numbers.

    production_path=True reproduces the finale: flags are read through
    mr_flags_from. production_path=False reproduces what the existing financial
    oracle does — the raw dict — and exists only so the divergence test can pin
    the difference rather than describe it.
    """
    aef = gs.get("active_event_flags") or {}
    flags = mr_flags_from(aef) if production_path else aef
    avg_slo = sum(float(b.get("social_license_score", 0) or 0) for b in bus) / max(len(bus), 1)
    avg_burnout = sum(float(b.get("staff_burnout_index", 0) or 0) for b in bus) / max(len(bus), 1)
    res = calculate_mr(
        flags=flags,
        avg_slo=avg_slo,
        avg_burnout=avg_burnout,
        workforce_readiness=float(gs.get("workforce_readiness", 50) or 50),
        synergy_multiplier=float(gs.get("synergy_multiplier", 1.0) or 1.0),
    )
    mr = res["mr"] if isinstance(res, dict) and "mr" in res else res
    mr_val = mr if isinstance(mr, (int, float)) else 1.0
    tv = calculate_terminal_value(bus, mr_val)
    arch = determine_archetype(mr_val)
    return {
        "m_r": _r(mr_val),
        "terminal_valuation": _r(tv["terminal_value"]) if isinstance(tv, dict) and "terminal_value" in tv else _r(tv),
        "archetype": arch.get("key") if isinstance(arch, dict) else arch,
        "bonuses_earned": sorted(res.get("bonuses_earned", [])) if isinstance(res, dict) else [],
    }


# ── the one driver ──────────────────────────────────────────────────────────
# run_path and final_state were separate copies of the same loop until Phase 3;
# they drifted the moment the sequence gained a step. There is one loop now and
# both callers ask it for a different part of the result.

def drive(
    path_name: str | None = None,
    *,
    spec: "RunSpec | None" = None,
    hooks: "MatrixHooks | None" = None,
    production_steps: bool = True,
    rules_version: str = DEFAULT_RULES_VERSION,
) -> tuple[list[dict], dict, list[dict]]:
    """Drive one seeded ten-round path.

    Returns (trace, final_global_state, final_bu_states).

    `hooks`, when given, is called at the points where the flag namespace changes
    hands; it is how tests/flag_probe.py observes and perturbs a run without this
    module growing a second code path for instrumentation.

    `rules_version` pins the run to a rule set, as router.commit_turn pins a
    session (Phase 4). The default is the semantics every fixture in
    golden/matrix was captured under; golden/matrix_2026_10 holds the same seven
    paths with every revival switched on.

    `production_steps=False` is the ORACLE-COMPATIBILITY MODE and is not a
    supported way to run the matrix. It drops the four steps Phase 3 added —
    pre_tick with server-derived crisis severity, the flags_set attach, the
    session-config stamps and _forward_persistent_flags — and holds crisis
    severity flat at the financial oracle's 20.0. It exists so
    test_harness_reproduces_the_financial_oracle_when_read_its_way can still make
    its claim: that this harness is the oracle's driver plus a NAMED set of
    production steps, not a different engine. Every fixture, every probe run and
    every reachability verdict uses the default.
    """
    if spec is None:
        if path_name is None:
            raise ValueError("drive() needs a path_name or a spec")
        spec = _spec_for(path_name)
    seed = spec.seed
    seed_string = spec.seed_string
    random.seed(seed)                      # belt and braces; the money path draws 0

    overrides = dict(spec.ped_overrides if spec.ped_overrides is not None
                     else PED_OVERRIDES)
    gs = make_initial_global(seed, seed_string)
    gs["active_event_flags"].update(spec.session_config or {})
    bus = make_initial_bus()
    if hooks:
        gs["active_event_flags"] = hooks.on_flags(gs["active_event_flags"], "initial", 0)
    previous_flags: dict = dict(gs["active_event_flags"])
    trace: list[dict] = []

    for rnd in range(1, N_ROUNDS + 1):
        gs["round_number"] = rnd
        gs["pedagogical_overrides"] = dict(overrides)
        decisions = _decisions(rnd, bus, spec)

        if production_steps:
            # router.py:2963 / :2988 — session difficulty and the god-mode systemic
            # switches are stamped onto the flags the engine reads, every commit.
            _aef = gs.setdefault("active_event_flags", {})
            _aef["difficulty_tier"] = DIFFICULTY_TIER
            _aef[SYSTEMIC_TOGGLES_FLAG] = _systemic_toggle_bag(overrides)
            _aef[RULES_FLAG] = rules_version          # router.py:2966

            # router.py:2894 + :2906 — the SERVER decides crisis severity (F-07)
            # and pre_tick applies the history-dependent multipliers on top of it.
            base_crisis = base_crisis_severity_for_round(rnd)
            pre_result = pre_tick(
                round_number=rnd, current_global=gs, current_bus=bus,
                decisions=decisions, crisis_severity=base_crisis, force_override_cfo=False,
            )
            if "validation_error" in pre_result:
                raise AssertionError(
                    f"{spec.label} R{rnd}: pre_tick rejected the decision — "
                    f"{pre_result['validation_error']}"
                )
            effective_crisis = pre_result.get("crisis_severity", base_crisis)
            pre_events = pre_result.get("pre_events", {}) or {}

            # router.py:2946-2960 (FLAG-3) — the chosen option's flags travel with
            # the decision, the only way the 58-rule sentiment map sees one.
            opt_flags = option_flags_for(rnd, _primary_choice(decisions), bus)
            if opt_flags:
                decisions[0]["flags_set"] = opt_flags
        else:
            effective_crisis = _ORACLE_CRISIS_SEVERITY
            pre_events = {}

        flags_before = dict(gs.get("active_event_flags") or {})

        result = process_tick(
            current_global=copy.deepcopy(gs),
            current_bus=copy.deepcopy(bus),
            decisions=decisions,
            dividends_paid=500_000 if rnd > 1 else 0,
            crisis_severity=effective_crisis,
            imitation_decay_rate=0.10,
            decision_paradigm="legacy_abc",
        )
        new_global, new_bus, events = result["global_state"], result["bu_states"], result["events"]

        events.update(pre_events)                                  # router.py:3036
        new_global.setdefault("active_event_flags", {})["stochastic_seed"] = seed_string
        if production_steps:
            _forward_persistent_flags(gs, new_global)              # router.py:3121
        new_global["pedagogical_overrides"] = dict(overrides)

        if hooks:
            # engine._assemble_global_state sets new_global["active_event_flags"]
            # to the events bag ITSELF (engine.py:4472, :4905) — the two names are
            # one object all the way through post_tick and run_new_engines, and
            # _forward_persistent_flags mutates it in place rather than rebinding.
            # Wrapping them as two objects de-aliases them, post_tick's writes stop
            # reaching the merge, and the run quietly diverges: measured,
            # group_reputation 58 -> 63 at R2 on every path. So wrap once and
            # install the same object in both places.
            aliased = new_global.get("active_event_flags") is events
            events = hooks.on_events(events, rnd)
            if aliased:
                new_global["active_event_flags"] = events
            else:
                new_global["active_event_flags"] = hooks.on_flags(
                    new_global["active_event_flags"], "post_tick_in", rnd)

        post_events = post_tick(round_number=rnd, global_state=new_global, bu_states=new_bus,
                                decisions=decisions, events=events,
                                previous_flags=previous_flags, decision_paradigm="legacy_abc")
        if production_steps:
            # router.py:3141. post_tick RETURNS its extra events and production
            # merges them; Phase 0 discarded the return value. Everything the R10
            # finale computes — mr_breakdown, terminal_value, the pathway premiums,
            # _finale_inputs — travels in it, so without this the finale ran and
            # then vanished, and the only terminal numbers the matrix had were the
            # ones terminal_snapshot reconstructed for itself.
            events.update(post_events or {})
            # router.py:3160-3168 — the engines' own inputs.
            events["decisions_raw"] = decisions
            events.setdefault("dividends_paid", 500_000 if rnd > 1 else 0)
            events["engagement_action"] = None
        new_engine_events = run_new_engines(round_number=rnd, global_state=new_global,
                                            bu_states=new_bus, events=events,
                                            previous_flags=previous_flags)
        if production_steps:
            events.update(new_engine_events or {})           # router.py:3174
            # router.py:3182-3186 (audit F-08 / SEAM-05). The finale runs inside
            # post_tick, BEFORE the NPC fines, agent hits and balance sheet land;
            # the restamp re-runs its valuation on the CLOSING state so the
            # persisted numbers are the graded ones. Skipping it left the fixtures
            # pinning a mid-pipeline snapshot.
            from flag_utils import finale_inputs_of
            if finale_inputs_of(events):
                from round_logic import restamp_finale_valuation
                restamp_finale_valuation(new_global, new_bus, events, previous_flags)
        _reporting_truth_resync(new_global, new_bus)

        # router.py:3322-3325 — history, then post_tick's rN_flags, then events.
        merged = dict(flags_before)
        merged.update(new_global.get("active_event_flags", {}))
        merged.update(events)
        if hooks:
            merged = hooks.on_flags(merged, "merged", rnd)
        new_global["active_event_flags"] = merged

        trace.append(_snapshot(rnd, new_global, new_bus))
        previous_flags = dict(new_global.get("active_event_flags") or {})
        if hooks:
            previous_flags = hooks.on_flags(previous_flags, "previous", rnd)
        gs, bus = new_global, new_bus

    return trace, gs, bus


class MatrixHooks:
    """The observation/perturbation seam `drive` calls. The default does nothing;
    tests/flag_probe.py subclasses it. Kept in this module so the driver has ONE
    shape whether or not it is being watched — an instrumented run that takes a
    different code path proves nothing about the uninstrumented one."""

    def on_flags(self, flags: dict, stage: str, rnd: int) -> dict:
        return flags

    def on_events(self, events: dict, rnd: int) -> dict:
        return events


def run_path(path_name: str, capture_terminal: bool = True,
             hooks: "MatrixHooks | None" = None,
             production_steps: bool = True,
             rules_version: str = DEFAULT_RULES_VERSION) -> list[dict]:
    """Drive one seeded ten-round path and return its snapshot list."""
    trace, gs, bus = drive(path_name, hooks=hooks, production_steps=production_steps,
                           rules_version=rules_version)
    if capture_terminal:
        trace = trace + [{
            # What the ENGINE graded — the numbers a team is shown.
            "finale": finale_snapshot(gs),
            # What this module reconstructs, kept because
            # test_terminal_mr_diverges_by_reader compares the two readers and
            # test_harness_reproduces_the_financial_oracle_when_read_its_way
            # compares this against the older fixture.
            "terminal": terminal_snapshot(gs, bus, production_path=True),
        }]
    return trace


def final_state(path_name: str, hooks: "MatrixHooks | None" = None,
                production_steps: bool = True,
                rules_version: str = DEFAULT_RULES_VERSION) -> tuple[dict, list[dict]]:
    """Re-run a path and hand back the raw end state, for tests that need to
    compute something the snapshot does not carry."""
    _trace, gs, bus = drive(path_name, hooks=hooks, production_steps=production_steps,
                            rules_version=rules_version)
    return gs, bus


def golden_path_for(path_name: str, rules_version: str = DEFAULT_RULES_VERSION) -> Path:
    return GOLDEN_DIRS[rules_version] / f"{path_name}.json"


def load_golden(path_name: str, rules_version: str = DEFAULT_RULES_VERSION):
    p = golden_path_for(path_name, rules_version)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def write_golden(path_name: str, trace, rules_version: str = DEFAULT_RULES_VERSION) -> None:
    p = golden_path_for(path_name, rules_version)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def first_diff(golden, current) -> str:
    if len(golden) != len(current):
        return f"entry count differs: golden={len(golden)} current={len(current)}"
    for g, c in zip(golden, current):
        if g != c:
            label = g.get("round", "terminal")
            for key in sorted(set(g) | set(c)):
                if g.get(key) != c.get(key):
                    return (f"first difference at {label}, key '{key}':\n"
                            f"  golden : {json.dumps(g.get(key), sort_keys=True)[:600]}\n"
                            f"  current: {json.dumps(c.get(key), sort_keys=True)[:600]}")
    return "no structural diff (unexpected)"
