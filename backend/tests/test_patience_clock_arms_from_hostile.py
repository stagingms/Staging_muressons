"""The F4 patience clock arms only from the first hostile-ish tier — audit
2026-09-04 F-16 · WP-16.

npc_stakeholders.determine_npc_action forced +1 escalation tier on any NPC
held at tier ≥ 1 ("Concerned") for PATIENCE_LIMIT rounds. Tier 0 needs
satisfaction/trust ≥ 70 for all four NPCs, which three of four never reach
even at reputation 85 / SLO 85 / CI 20 — so with stakeholder_uncertainty
enabled (the production default) an even-investment team took ≈3.5 forced
hostile actions, −16.8 group reputation and, near the jittered boundary, a
$5–25M regulator fine, none of it attributable to a decision. The clock now
arms from tier 2. PATIENCE_LIMIT stays 3: the tier, not the limit, was the
defect (calibration call, stated).

The production-chain case below is ~/audit_scratch/soc/p10 as a test: an
even 100%-of-pool team, production toggles, real seed, F4 ON.
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

_HOSTILE = ("hostile", "adversarial", "enforcement", "legal", "protest")


def test_the_clock_arms_from_tier_two():
    import npc_stakeholders as N
    assert N.PATIENCE_ARMS_FROM_TIER == 2
    import inspect
    src = inspect.getsource(N.determine_npc_action)
    assert "tier_idx >= PATIENCE_ARMS_FROM_TIER" in src
    assert "tier_idx >= 1 and npc_state" not in src


def _run_even_team(cohort_seed: int, uncertainty: bool):
    """The production call chain (dry_run helpers), even 100% team, option B."""
    import dry_run
    from dry_run import _decisions, base_crisis_severity_for_round, pre_tick, post_tick, run_new_engines, \
        CSF_POOL_TREASURY_FRACTION, CSF_POOL_FLOOR
    from engine import process_tick
    from config import DEFAULT_IMITATION_DECAY_RATE
    from bu_profiles import build_bu_states
    import database_memory as dm
    import npc_stakeholders as N
    import autonomous_agents as A
    seed = dm._load_seed("generic")
    sg = seed["global_state"]
    gs = {"round_number": 1, "corporate_treasury": sg["corporate_treasury_usd"], "group_reputation": sg["group_reputation_score"],
          "synergy_multiplier": sg["group_synergy_multiplier"], "cost_of_capital": sg["cost_of_capital_rate"], "active_event_flags": {},
          "historical_ebitda": 0, "tco2e_emissions": 0, "green_transition_fund": 0, "tipping_point_active": False,
          "pending_capex_projects": [], "inflation_index": 0.025, "workforce_readiness": 50.0, "momentum_history": []}
    bus = build_bu_states()
    ped = {"black_swan_events_enabled": False, "decision_timer_enabled": False,
           "stakeholder_uncertainty_enabled": uncertainty}
    rng = random.Random(cohort_seed)
    random.seed(cohort_seed)
    gs["active_event_flags"]["stochastic_seed"] = f"f16-{cohort_seed}"
    strat = {"capex_frac": 1.0, "dividends": 0, "scorer": "balanced", "choice_map": None}
    # no betrayal flags: isolate the clock
    real_bet_n, real_bet_a = N.detect_betrayal, A.detect_betrayal
    N.detect_betrayal = lambda ev: False
    A.detect_betrayal = lambda ev: False
    out = []
    try:
        for rnd in range(1, 11):
            gs["round_number"] = rnd
            gs["pedagogical_overrides"] = dict(ped)
            decs = _decisions(rnd, bus, gs["corporate_treasury"], strat, rng)
            for d in decs:
                d["choice_selected"] = "option_b"
            sev = base_crisis_severity_for_round(rnd)
            t = float(gs["corporate_treasury"])
            emerg = bool(t * CSF_POOL_TREASURY_FRACTION < CSF_POOL_FLOOR)
            pre = pre_tick(round_number=rnd, current_global=gs, current_bus=bus, decisions=decs, crisis_severity=sev, force_override_cfo=False)
            if "validation_error" in pre:
                for d in decs:
                    d["capex_allocated"] = 1.0
                    d["investment_ratio"] = 0.0
                pre = pre_tick(round_number=rnd, current_global=gs, current_bus=bus, decisions=decs, crisis_severity=sev, force_override_cfo=True)
            sev = pre.get("crisis_severity", sev)
            tick = process_tick(current_global=gs, current_bus=bus, decisions=decs, dividends_paid=0, crisis_severity=sev,
                                imitation_decay_rate=DEFAULT_IMITATION_DECAY_RATE, decision_paradigm="legacy_abc", emergency_credit_used=emerg)
            ngs, nbus, ev = tick["global_state"], tick["bu_states"], tick["events"]
            ev.update(pre.get("pre_events", {}))
            ngs.setdefault("active_event_flags", {})["stochastic_seed"] = gs["active_event_flags"]["stochastic_seed"]
            pe = post_tick(round_number=rnd, global_state=ngs, bu_states=nbus, decisions=decs, events=ev,
                           previous_flags=gs.get("active_event_flags", {}), decision_paradigm="legacy_abc")
            if isinstance(pe, dict):
                ev.update(pe)
            ngs["pedagogical_overrides"] = dict(ped)
            extra = run_new_engines(round_number=rnd, global_state=ngs, bu_states=nbus, events=ev)
            npc = extra.get("npc_stakeholders") or {}
            acts = npc.get("npc_actions") or []
            out.append({
                "r": rnd,
                "hostile": [f"{a.get('npc_id')}:{a.get('action')}" for a in acts if a.get("action") in _HOSTILE],
                "fine": npc.get("regulatory_fine") or 0,
                "rep": round(ngs["group_reputation"], 1),
            })
            gs, bus = ngs, nbus
    finally:
        N.detect_betrayal, A.detect_betrayal = real_bet_n, real_bet_a
    return out


@pytest.mark.parametrize("cohort_seed", [90_000, 90_007, 90_014])
def test_an_even_investment_team_is_never_forced_hostile_on_a_timer(cohort_seed):
    on = _run_even_team(cohort_seed, uncertainty=True)
    off = _run_even_team(cohort_seed, uncertainty=False)
    hostile_on = [x for x in on if x["hostile"]]
    assert not hostile_on, f"F4 ON forced hostile actions on an even team: {hostile_on}"
    assert sum(x["fine"] for x in on) == 0
    # and the clock costs the team nothing relative to F4 OFF at R10
    assert abs(on[-1]["rep"] - off[-1]["rep"]) < 0.5, (on[-1], off[-1])
