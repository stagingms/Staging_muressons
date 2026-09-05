"""
Muressons — Stakeholder / SLO Golden Round-Trace Oracle (SPEC v1, Phase 0)
═══════════════════════════════════════════════════════════════════════════
Regression oracle for the stakeholder ↔ Social-License-to-Operate segment.

WHY THIS EXISTS
    Phases 1–6 of the stakeholder realism upgrade mutate SLO, reputation and
    NPC state. This test pins the *current* behaviour: a fixed, seeded 10-round
    run is captured to a golden JSON, and every later phase must diff against it.
    With all `stakeholder_*_enabled` toggles OFF (their Phase-0 default), the
    trace MUST stay byte-identical to pre-change `main` — that is the contract
    that lets each phase "land dark" without disturbing live behaviour.

WHAT IT DRIVES
    The real pipeline: `engine.process_tick` (SLO decay / pillar deltas / strike)
    followed by `round_logic.run_new_engines` (NPC tick, cascades, tipping).
    Engine sub-state carry-forward is replicated exactly as production does it —
    `process_tick` rebuilds global_state from a whitelist (dropping
    `npc_stakeholders`), and `run_new_engines` re-seeds it — so this oracle also
    documents the current memoryless-NPC behaviour that Phase 1 (F1) will change.

DETERMINISM
    Reproducibility comes from the GAME-4 cohort `stochastic_seed` (set in the
    initial state, exactly as a real cohort carries it), which makes every
    `event_rng` stream deterministic. Out-of-scope engines that roll on the bare
    global `random` module are disabled (see `_PED_OVERRIDES`). Captured floats
    are rounded (`_ROUND_DP`) so the oracle is stable across Python/OS float
    formatting while still catching any real mechanical change.

REBASELINE (deliberate, reviewed)
    Regenerate the golden after an *intended* behaviour change:
        MURESSONS_REBASELINE_GOLDEN=1 pytest tests/test_stakeholder_golden_trace.py
    or run this file directly:  python tests/test_stakeholder_golden_trace.py
    The JSON diff belongs in the same commit/PR as the change that caused it.
"""

from __future__ import annotations

import copy
import json
import os
import random
import sys
from pathlib import Path

import pytest

# ── Path / env setup (mirrors the other engine tests) ─────────────
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

from engine import process_tick               # noqa: E402
from round_logic import run_new_engines        # noqa: E402

# ── Oracle configuration ──────────────────────────────────────────
_GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
_GOLDEN_PATH = _GOLDEN_DIR / "stakeholder_slo_trace.json"
_SEED = 20260712          # fixed cohort seed — do not change casually
_ROUND_DP = 4             # capture precision (decimal places)
_N_ROUNDS = 10

# Overrides applied every round.
#   - black-swans / decision timer OFF: keep the oracle focused and quiet.
#   - org_politics / board_governance / supply_chain OFF: these roll on the bare
#     global `random` module (un-seeded) and are the only entropy sources once
#     the GAME-4 `stochastic_seed` is set. They are out of scope for the
#     stakeholder ↔ SLO segment, so disabling them keeps the trace deterministic
#     and focused. Stakeholder-relevant stochastic paths (materiality shocks,
#     micro-strike, NPC cascades) stay ON — they use seeded `event_rng`.
#   - the six stakeholder_* toggles are pinned OFF (their Phase-0 default) so the
#     intent is legible and an accidental default-flip shows up as a golden diff.
_PED_OVERRIDES = {
    "black_swan_events_enabled": False,
    "decision_timer_enabled": False,
    "org_politics_enabled": False,
    "board_governance_enabled": False,
    "supply_chain_network_enabled": False,
    "stakeholder_memory_enabled": False,
    "stakeholder_slo_feedback_enabled": False,
    "stakeholder_engagement_enabled": False,
    "stakeholder_coalitions_enabled": False,
    "stakeholder_uncertainty_enabled": False,
    "stakeholder_intel_ui_enabled": False,
}


# ── Deterministic initial state ───────────────────────────────────
def _make_initial_global() -> dict:
    return {
        "round_number": 1,
        "corporate_treasury": 50_000_000,
        "group_reputation": 60.0,
        "synergy_multiplier": 0.35,
        "cost_of_capital": 0.05,
        # `stochastic_seed` is what a real cohort carries: it makes every GAME-4
        # `event_rng` stream deterministic. Without it, event_rng falls back to a
        # system-seeded RNG (rng_util) and shocks roll on entropy — the exact
        # source of cross-run drift this oracle must not have.
        "active_event_flags": {"stochastic_seed": f"golden-{_SEED}"},
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
    bus = []
    for bu_id, cfg in configs.items():
        bus.append({
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
        })
    return bus


# A fixed, deterministic decision script that deliberately exercises both
# improving and neglect trajectories so SLO moves in both directions.
_CHOICE_BY_ROUND = {
    1: "option_b", 2: "option_a", 3: "option_c", 4: "option_a", 5: "option_b",
    6: "option_c", 7: "option_a", 8: "option_b", 9: "option_c", 10: "option_a",
}
# Per-BU investment ratios chosen to straddle the SLO decay/growth thresholds
# (>=0.30 grows, <0.15 decays) so the oracle covers both branches.
_INVEST_BY_BU = {"pharma": 0.7, "electronics": 0.05, "consumer_goods": 0.4, "software": 0.1}


def _decisions_for_round(rnd: int, bus: list[dict]) -> list[dict]:
    choice = _CHOICE_BY_ROUND.get(rnd, "option_b")
    return [
        {
            "bu_id": bu["bu_id"],
            "investment_ratio": _INVEST_BY_BU.get(bu["bu_id"], 0.3),
            "capex_allocated": 1_500_000 if _INVEST_BY_BU.get(bu["bu_id"], 0.3) >= 0.15 else 0,
            "choice_selected": choice,
        }
        for bu in bus
    ]


def _r(x):
    """Round floats for stable capture; pass through non-numerics."""
    return round(float(x), _ROUND_DP) if isinstance(x, (int, float)) else x


def _snapshot(rnd: int, gs: dict, bus: list[dict]) -> dict:
    """Capture the SLO / reputation / NPC surface for one round."""
    npc_root = (gs.get("npc_stakeholders") or {}).get("npcs", {}) or {}
    npcs = {}
    for npc_id in sorted(npc_root):
        nd = npc_root[npc_id]
        npcs[npc_id] = {
            "satisfaction": _r(nd.get("satisfaction", 50)),
            # `trust` is dead state today (populated by F1/Phase 1). Captured so
            # the oracle records the transition when memory ships.
            "trust": _r(nd["trust"]) if isinstance(nd.get("trust"), (int, float)) else None,
            "escalation_level": nd.get("escalation_level"),
        }
    return {
        "round": rnd,
        "group_reputation": _r(gs.get("group_reputation", 0)),
        "bus": [
            {
                "bu_id": bu["bu_id"],
                "social_license_score": _r(bu.get("social_license_score", 0)),
                "reputation_score": _r(bu.get("reputation_score", 0)),
                "governance_risk_score": _r(bu.get("governance_risk_score", 0)),
            }
            for bu in sorted(bus, key=lambda b: b["bu_id"])
        ],
        "npcs": npcs,
    }


def generate_trace() -> list[dict]:
    """
    Run the fixed, seeded 10-round simulation through the real pipeline and
    return the per-round snapshot list. Deterministic and side-effect free.

    Randomness is pinned on BOTH channels the engine uses: the GAME-4
    `event_rng` streams (via `stochastic_seed`, re-merged each round below) and
    the bare global `random` module used by a few engines — seeded here so the
    oracle does not depend on interpreter entropy.
    """
    random.seed(_SEED)

    gs = _make_initial_global()
    bus = _make_initial_bus()
    trace: list[dict] = []

    for rnd in range(1, _N_ROUNDS + 1):
        gs["round_number"] = rnd
        gs["pedagogical_overrides"] = dict(_PED_OVERRIDES)
        decisions = _decisions_for_round(rnd, bus)

        result = process_tick(
            current_global=copy.deepcopy(gs),
            current_bus=copy.deepcopy(bus),
            decisions=decisions,
            dividends_paid=500_000 if rnd > 1 else 0,
            crisis_severity=40.0,
            imitation_decay_rate=0.10,
            decision_paradigm="legacy_abc",
        )
        new_global = result["global_state"]
        new_bus = result["bu_states"]
        events = result["events"]

        # `process_tick` rebuilds active_event_flags from `events` and drops
        # `stochastic_seed`; production re-merges the persistent flags in the
        # router (`merged_flags`), which this harness bypasses. Re-inject the
        # seed so round 2+ `event_rng` streams stay deterministic instead of
        # falling back to interpreter entropy.
        new_global.setdefault("active_event_flags", {})["stochastic_seed"] = f"golden-{_SEED}"

        # Replicate production carry-forward: run_new_engines runs on the
        # freshly-assembled global_state (which whitelisted away npc_stakeholders)
        # and re-seeds the stakeholder engines, mutating new_global/new_bus.
        new_global["pedagogical_overrides"] = dict(_PED_OVERRIDES)
        try:
            run_new_engines(
                round_number=rnd,
                global_state=new_global,
                bu_states=new_bus,
                events=events,
            )
        except Exception as exc:  # engines are individually try/excepted; belt-and-braces
            trace.append({"round": rnd, "error": f"run_new_engines raised: {exc}"})
            break

        trace.append(_snapshot(rnd, new_global, new_bus))

        # The persisted next-round state is new_global (with engine sub-states),
        # exactly as commit_turn stores it.
        gs = new_global
        bus = new_bus

    return trace


def _load_golden():
    if not _GOLDEN_PATH.exists():
        return None
    with open(_GOLDEN_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_golden(trace: list[dict]) -> None:
    _GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    with open(_GOLDEN_PATH, "w", encoding="utf-8") as fh:
        json.dump(trace, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _first_diff(golden: list[dict], current: list[dict]) -> str:
    if len(golden) != len(current):
        return f"round count differs: golden={len(golden)} current={len(current)}"
    for g, c in zip(golden, current):
        if g != c:
            return (
                f"round {g.get('round')} differs:\n"
                f"  golden : {json.dumps(g, sort_keys=True)}\n"
                f"  current: {json.dumps(c, sort_keys=True)}"
            )
    return "no structural diff (unexpected)"


# ═══════════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════════
def test_trace_is_deterministic():
    """Two runs of the same seeded pipeline must be identical."""
    a = generate_trace()
    b = generate_trace()
    assert a == b, "Stakeholder/SLO trace is not deterministic across runs"


def test_golden_trace_matches():
    """
    Current pipeline output must equal the committed golden trace.
    On first run (or with MURESSONS_REBASELINE_GOLDEN=1) the golden is written
    and the test is skipped so the baseline can be reviewed and committed.
    """
    current = generate_trace()
    rebaseline = os.environ.get("MURESSONS_REBASELINE_GOLDEN") == "1"
    golden = None if rebaseline else _load_golden()

    if golden is None:
        _write_golden(current)
        pytest.skip(
            f"Golden baseline written to {_GOLDEN_PATH.relative_to(_BACKEND_DIR)} "
            f"({len(current)} rounds). Review and commit it; the test enforces it thereafter."
        )

    assert current == golden, (
        "Stakeholder/SLO golden trace drift detected. If this change is "
        "intentional, rebaseline with MURESSONS_REBASELINE_GOLDEN=1 and commit "
        "the new golden alongside the change.\n\nFirst diff:\n" + _first_diff(golden, current)
    )


def test_toggles_default_off():
    """Phase-0 contract: the six stakeholder toggles ship OFF by default."""
    from pedagogical_engine import DEFAULT_PEDAGOGICAL_TOGGLES as D
    # Updated 2026-09-01 (EVAL_Stakeholder_SLO rec 1+2, owner ruling): the
    # realism waves ship ON; only the F6 intel rail stays opt-in. This trace's
    # own harness still pins its toggles explicitly (see _BASE_TOGGLES above),
    # so the golden numbers are independent of these platform defaults.
    # Updated 2026-09-02 (audit F-11, owner ruling): F2 continuous NPC pressure
    # is back to OFF by default — with it ON the disciplined script could not
    # reach the M_R >= 1.2 the MODEL_CARD promises. Facilitators opt in per
    # cohort. See test_stakeholder_defaults.py for the same pin.
    for key in (
        "stakeholder_memory_enabled",
        "stakeholder_engagement_enabled",
        "stakeholder_coalitions_enabled",
        "stakeholder_uncertainty_enabled",
    ):
        assert key in D, f"missing wave toggle: {key}"
        assert D[key] is True, f"wave toggle must default ON: {key}"
    assert D["stakeholder_slo_feedback_enabled"] is False, "F2 pressure is opt-in (F-11)"
    assert D["stakeholder_intel_ui_enabled"] is False, "F6 rail stays opt-in"


def test_npc_state_carries_forward():
    """
    Phase-1 §1.7 prerequisite: the `npc_stakeholders` engine sub-dict must survive
    the `process_tick` boundary instead of being re-initialised every round.

    Observable proxy that needs no `trust` field: `process_npc_tick` appends one
    entry to each NPC's `interactions` list per round, so after N rounds the list
    length must equal N. Before the `_assemble_global_state` carry-forward fix the
    sub-dict was rebuilt each tick and the length stayed pinned at 1 — this test is
    the regression guard for that fix (and for `trust` persisting once F1 lands).
    """
    random.seed(_SEED)
    gs = _make_initial_global()
    bus = _make_initial_bus()
    per_round_lengths: list[dict[str, int]] = []

    for rnd in range(1, 4):  # 3 rounds is enough to prove accumulation vs reset
        gs["round_number"] = rnd
        gs["pedagogical_overrides"] = dict(_PED_OVERRIDES)
        result = process_tick(
            current_global=copy.deepcopy(gs),
            current_bus=copy.deepcopy(bus),
            decisions=_decisions_for_round(rnd, bus),
            dividends_paid=500_000 if rnd > 1 else 0,
            crisis_severity=40.0,
            imitation_decay_rate=0.10,
            decision_paradigm="legacy_abc",
        )
        new_global, new_bus, events = result["global_state"], result["bu_states"], result["events"]
        new_global.setdefault("active_event_flags", {})["stochastic_seed"] = f"golden-{_SEED}"
        new_global["pedagogical_overrides"] = dict(_PED_OVERRIDES)
        run_new_engines(round_number=rnd, global_state=new_global, bu_states=new_bus, events=events)

        npcs = (new_global.get("npc_stakeholders") or {}).get("npcs", {})
        assert npcs, "npc_stakeholders produced no NPC state — engine wiring changed"
        per_round_lengths.append({k: len(v.get("interactions", [])) for k, v in npcs.items()})
        gs, bus = new_global, new_bus

    for npc_id, length in per_round_lengths[-1].items():
        assert length == 3, (
            f"NPC '{npc_id}' has {length} interactions after 3 rounds, expected 3 — "
            f"npc_stakeholders is being re-initialised each round (SPEC §1.7 regression: "
            f"_assemble_global_state must carry it forward). Per-round lengths: "
            f"{[d.get(npc_id) for d in per_round_lengths]}"
        )


def test_trust_integrator_asymmetry_and_scar():
    """
    F1 §1.2 trust integrator: rises slower than it falls, and a betrayal scars it
    and caps recovery for exactly SCAR_DURATION rounds. Pure-function unit test.
    """
    from npc_stakeholders import update_trust
    c = dict(gain_rate=0.25, loss_rate=0.55, scar_immediate=12.0, scar_duration=3, scar_ceiling=60.0)

    # First observation seeds the stock at current mood, not a flat 50.
    seeded = {}
    assert update_trust(seeded, 42.0, False, 1, **c) == 42.0
    assert seeded["trust_initialised"] is True

    # Equal-magnitude gaps: a drop moves trust further than an equal rise.
    up = {"trust": 50.0, "trust_initialised": True, "scar_until": 0}
    dn = {"trust": 50.0, "trust_initialised": True, "scar_until": 0}
    t_up = update_trust(up, 70.0, False, 2, **c)   # +20 gap
    t_dn = update_trust(dn, 30.0, False, 2, **c)   # -20 gap
    assert t_up == round(50 + 0.25 * 20, 2)
    assert t_dn == round(50 - 0.55 * 20, 2)
    assert (t_up - 50.0) < (50.0 - t_dn), "trust must fall faster than it rises"

    # Betrayal at round 5: immediate hit + recovery capped at ceiling through R8.
    sc = {"trust": 80.0, "trust_initialised": True, "scar_until": 0}
    t_scar = update_trust(sc, 80.0, True, 5, **c)
    assert sc["scar_until"] == 8
    assert t_scar <= 60.0
    # Within the scar window, high satisfaction still cannot lift trust past the cap.
    assert update_trust(sc, 100.0, False, 7, **c) <= 60.0
    # After the window closes the ceiling lifts.
    sc["trust"] = 59.0
    assert update_trust(sc, 100.0, False, 9, **c) > 60.0


def test_sentiment_bridge_blends_satisfaction():
    """
    F1 §1.4 bridge: with bridge_weight > 0, a named NPC's satisfaction is pulled
    toward the matching portfolio sentiment cohort's attitude_score; with
    bridge_weight == 0 (or no sentiment list, or an unmatched NPC) it is untouched,
    so the memory-off path and the golden trace are unaffected.
    """
    from npc_stakeholders import calc_npc_satisfaction

    npc_state = {"profile": {"satisfaction_drivers": [("social_license_score", 0.4, 50)]}}
    bus = [{"bu_id": "b", "social_license_score": 50}]  # metric satisfaction == 50 exactly

    # bridge off -> pure metric
    base, _ = calc_npc_satisfaction("community_leader", npc_state, {}, bus, bridge_weight=0.0)
    assert base == 50.0

    # bridge on but no sentiment list -> no-op
    none_present, _ = calc_npc_satisfaction("community_leader", npc_state, {}, bus, bridge_weight=0.3)
    assert none_present == 50.0

    # bridge on with a hostile community cohort (20) pulls satisfaction down;
    # a non-matching regulator cohort (90) is ignored.
    gs = {"sentiment_stakeholders": [
        {"id": "local_community_deccan", "attitude_score": 20.0},
        {"id": "eu_regulator", "attitude_score": 90.0},
    ]}
    blended, diag = calc_npc_satisfaction("community_leader", npc_state, gs, bus, bridge_weight=0.3)
    assert blended == round(0.7 * 50 + 0.3 * 20, 2) == 41.0
    assert diag["sentiment_bridge"] == 20.0

    # unmatched NPC id -> no bridge even with sentiment present
    unmatched, _ = calc_npc_satisfaction("nonexistent_npc", npc_state, gs, bus, bridge_weight=0.3)
    assert unmatched == 50.0


def test_slo_feedback_tier_pressure_and_guards():
    """
    F2 §2.2–2.3: continuous tier→SLO feedback applies per-tier pressure to the
    attached BUs, suppresses NPCs that cascaded this round (no double count), is
    idempotent within a round, and clamps to [0, 100].
    """
    from npc_stakeholders import apply_stakeholder_slo_feedback

    reg_levels = [{"threshold": 70, "action": "satisfied"}, {"threshold": 50, "action": "monitoring"},
                  {"threshold": 30, "action": "investigation"}, {"threshold": 0, "action": "enforcement"}]
    com_levels = [{"threshold": 70, "action": "cooperative"}, {"threshold": 50, "action": "watchful"},
                  {"threshold": 30, "action": "protest"}, {"threshold": 0, "action": "legal"}]

    def npc(action, levels):
        return {"profile": {"escalation_levels": levels}, "escalation_level": action}

    def fresh_bus():
        return [{"bu_id": "pharma", "social_license_score": 50, "water_dependency": 30},
                {"bu_id": "agri", "social_license_score": 50, "water_dependency": 80}]

    # regulator "investigation" (tier 2 → −2, all BUs); community "legal" (tier 3 → −3.5, water BU only)
    state = {"npcs": {"regulator": npc("investigation", reg_levels),
                      "community_leader": npc("legal", com_levels)}}
    bus = fresh_bus()
    deltas = apply_stakeholder_slo_feedback(state, bus, 1, cascaded_npc_ids=set(), coupling=1.0)
    slo = {b["bu_id"]: b["social_license_score"] for b in bus}
    assert slo["pharma"] == 48.0                       # regulator −2 only
    assert slo["agri"] == 44.5                          # regulator −2 + community −3.5
    assert deltas["agri"]["community_leader"] == -3.5
    assert "community_leader" not in deltas.get("pharma", {})  # not attached to low-water BU

    # idempotent within the round
    assert apply_stakeholder_slo_feedback(state, bus, 1, cascaded_npc_ids=set(), coupling=1.0) == {}
    assert {b["bu_id"]: b["social_license_score"] for b in bus} == slo

    # no double count: a cascaded NPC is suppressed here (its delta is applied by the cascade)
    bus2 = fresh_bus()
    state2 = {"npcs": {"regulator": npc("investigation", reg_levels),
                       "community_leader": npc("legal", com_levels)}}
    apply_stakeholder_slo_feedback(state2, bus2, 1, cascaded_npc_ids={"regulator"}, coupling=1.0)
    slo2 = {b["bu_id"]: b["social_license_score"] for b in bus2}
    assert slo2["pharma"] == 50.0                       # regulator suppressed, community not attached
    assert slo2["agri"] == 46.5                          # only community −3.5

    # cooperative tier lifts SLO and clamps at 100
    bus3 = [{"bu_id": "x", "social_license_score": 99.5, "water_dependency": 10}]
    apply_stakeholder_slo_feedback({"npcs": {"regulator": npc("satisfied", reg_levels)}},
                                   bus3, 1, cascaded_npc_ids=set(), coupling=1.0)
    assert bus3[0]["social_license_score"] == 100.0


def test_engagement_promises_kept_and_broken():
    """
    F5 §5.2: a public pledge costs treasury, bumps trust now, and registers a
    promise; at the due round a kept promise pays trust + SLO + reputation, a
    broken one fires the F1 betrayal scar and a reputation ding, and each promise
    resolves exactly once.
    """
    from stakeholder_engagement import apply_engagement_action, resolve_promises

    consts = {
        "cost": {"town_hall": 500_000, "public_pledge": 1_000_000, "private_commitment": 300_000},
        "trust": {"town_hall": 3.0, "public_pledge": 6.0, "private_commitment": 4.0},
        "default_horizon": 3, "kept_trust_bonus": 8.0, "kept_slo_credit": 4.0, "kept_rep_credit": 3.0,
        "broken_rep_ding": 6.0, "scar_immediate": 12.0, "scar_duration": 3, "scar_ceiling": 60.0,
    }

    def state():
        return {"npcs": {"community_leader": {"profile": {"escalation_levels": []}, "trust": 50.0}},
                "promises": []}

    bus = [{"bu_id": "agri", "social_license_score": 60, "water_dependency": 80}]
    gs = {"corporate_treasury": 50_000_000, "group_reputation": 60.0}

    # Public pledge: cost deducted, trust +6, promise registered open.
    st = state()
    r = apply_engagement_action(st, gs, {
        "type": "public_pledge", "npc_id": "community_leader",
        "metric": "group_reputation", "target": 65, "horizon": 2,
    }, 1, consts=consts)
    assert gs["corporate_treasury"] == 49_000_000
    assert st["npcs"]["community_leader"]["trust"] == 56.0
    assert len(st["promises"]) == 1 and st["promises"][0]["due_round"] == 3
    assert r["promise"]["state"] == "open"

    # Kept: reputation (70) >= target 65 at the due round → trust/SLO/rep credit.
    gs["group_reputation"] = 70.0
    res = resolve_promises(st, gs, bus, 3, consts=consts)
    assert len(res) == 1 and res[0]["state"] == "kept"
    assert st["npcs"]["community_leader"]["trust"] == 64.0    # 56 + 8
    assert gs["group_reputation"] == 73.0                      # +3
    assert bus[0]["social_license_score"] == 64.0             # +4 to the attached water BU
    assert resolve_promises(st, gs, bus, 4, consts=consts) == []  # resolves once

    # Broken: metric below target at the due round → scar + reputation ding.
    gs2 = {"corporate_treasury": 10_000_000, "group_reputation": 60.0}
    st2 = state(); st2["npcs"]["community_leader"]["trust"] = 70.0
    apply_engagement_action(st2, gs2, {
        "type": "public_pledge", "npc_id": "community_leader",
        "metric": "group_reputation", "target": 80, "horizon": 1,
    }, 2, consts=consts)
    gs2["group_reputation"] = 50.0
    res2 = resolve_promises(st2, gs2, bus, 3, consts=consts)
    cl = st2["npcs"]["community_leader"]
    assert res2[0]["state"] == "broken"
    assert cl["trust"] == 64.0            # 76 − 12 scar
    assert cl["scar_until"] == 6          # round 3 + duration 3
    assert gs2["group_reputation"] == 44.0  # −6 ding

    # Invalid action → reported, no treasury change.
    gs3 = {"corporate_treasury": 1000, "group_reputation": 50}
    er = apply_engagement_action(state(), gs3, {"type": "bogus", "npc_id": "community_leader"}, 1, consts=consts)
    assert er.get("error") == "invalid_engagement" and gs3["corporate_treasury"] == 1000


def test_coalition_pressure_and_strike_coupling():
    """
    F3 §3.2/§3.5: ≥2 salient hostile stakeholders form a coalition with pressure
    > 0; the coalition multiplier makes strike probability strictly higher than a
    lone actor, and strike probability still clamps at 1.0.
    """
    from systemic_risk_engine import evaluate_coalition_and_contagion
    from engine import calc_strike_probability

    levels = [{"threshold": 70, "action": "a"}, {"threshold": 50, "action": "b"},
              {"threshold": 30, "action": "c"}, {"threshold": 0, "action": "d"}]
    sal = {"power": 0.9, "urgency": 0.9, "legitimacy": 0.9}  # mean 0.9

    def npc(action):
        return {"profile": {"escalation_levels": levels, "salience": sal},
                "escalation_level": action, "satisfaction": 20.0, "trust": 20.0}

    # one hostile actor → no coalition
    r1 = evaluate_coalition_and_contagion({"npcs": {"regulator": npc("d")}}, [], tier_min=2)
    assert r1["coalition_pressure"] == 0.0 and r1["members"] == ["regulator"]

    # two hostile actors → pressure = min(1, mean_sal * (count-1)) = 0.9
    r2 = evaluate_coalition_and_contagion(
        {"npcs": {"regulator": npc("d"), "journalist": npc("c")}}, [], tier_min=2)
    assert r2["coalition_pressure"] == 0.9 and set(r2["members"]) == {"regulator", "journalist"}

    # strike coupling: coalition multiplier raises the probability, and it clamps
    base_p = calc_strike_probability(0.1, 50)
    coal_p = calc_strike_probability(0.1, 50, coalition_multiplier=1 + 0.9 * 0.5)
    assert coal_p > base_p
    assert calc_strike_probability(0.9, 0, coalition_multiplier=5.0) == 1.0


def test_contagion_hop_cap_one_wave():
    """
    F3 §3.2: a fired cascade nudges the NPCs named in its cascading_triggers once
    (one wave, hop cap 1) — the source is untouched and nudges do not re-propagate.
    """
    from systemic_risk_engine import evaluate_coalition_and_contagion

    levels = [{"threshold": 70, "action": "a"}, {"threshold": 0, "action": "d"}]

    def npc(action):
        return {"profile": {"escalation_levels": levels, "salience": {"power": .8, "urgency": .8, "legitimacy": .8}},
                "escalation_level": action, "satisfaction": 50.0, "trust": 50.0}

    state = {"npcs": {"activist_investor": npc("d"), "journalist": npc("a"), "regulator": npc("a")}}
    cascades = [{"npc_id": "activist_investor",
                 "effects": {"cascading_triggers": ["journalist_hostile", "regulator_monitoring"]}}]
    r = evaluate_coalition_and_contagion(state, cascades, tier_min=2, contagion_nudge=5.0)

    assert state["npcs"]["journalist"]["satisfaction"] == 45.0
    assert state["npcs"]["journalist"]["trust"] == 45.0
    assert state["npcs"]["regulator"]["satisfaction"] == 45.0
    assert r["contagion_nudges"] == {"journalist": -5.0, "regulator": -5.0}
    # the source is not self-nudged
    assert state["npcs"]["activist_investor"]["satisfaction"] == 50.0


def test_threshold_jitter_seeded_and_effective():
    """
    F4 §4.2: threshold offsets are drawn deterministically from the cohort seed
    (same seed → identical for every team, different seed → different) and, when
    applied, actually move the escalation boundary.
    """
    from npc_stakeholders import _draw_threshold_offsets, determine_npc_action

    a = _draw_threshold_offsets("regulator", "seed-A", 4.0)
    b = _draw_threshold_offsets("regulator", "seed-A", 4.0)
    c = _draw_threshold_offsets("regulator", "seed-B", 4.0)
    assert a == b                                   # fair: identical across teams
    assert a != c                                   # unknown: different per cohort seed
    assert len(a) == 4 and all(-4.0 <= o <= 4.0 for o in a)

    levels = [{"threshold": 70, "action": "cooperative", "label": "C"},
              {"threshold": 50, "action": "watchful", "label": "W"},
              {"threshold": 30, "action": "protest", "label": "P"},
              {"threshold": 0, "action": "legal", "label": "L"}]
    prof = {"escalation_levels": levels, "dialogue_templates": {}, "name": "n", "title": "t", "icon": "i"}

    # EVAL rec 3 (2026-09-01): escalation is staged — a standing start caps at
    # one tier past cooperative, which would mask the jitter here. Seed the
    # state as "was watchful last round" so the jittered drop to protest is a
    # legal one-tier move and the test keeps measuring the BOUNDARY, not the
    # stager.
    base = determine_npc_action("x", {"profile": prof, "last_tier": 1}, 52.0, {}, 1)["action"]
    jit = determine_npc_action("x", {"profile": prof, "last_tier": 1}, 52.0, {}, 1,
                               threshold_offsets=[0, 4, 0, 0])["action"]
    assert base == "watchful"       # 52 ≥ base watchful threshold 50
    assert jit == "protest"         # 52 < jittered watchful threshold 54 → drops a tier


def test_patience_forces_escalation_and_cooperative_resets():
    """
    F4 §4.2 patience clock: a stakeholder held at a wary tier for PATIENCE_LIMIT
    rounds escalates one tier even on a flat metric; recovering to cooperative
    resets the clock.
    """
    from npc_stakeholders import determine_npc_action

    levels = [{"threshold": 70, "action": "cooperative", "label": "C"},
              {"threshold": 50, "action": "watchful", "label": "W"},
              {"threshold": 30, "action": "protest", "label": "P"},
              {"threshold": 0, "action": "legal", "label": "L"}]
    st = {"profile": {"escalation_levels": levels, "dialogue_templates": {}, "name": "n", "title": "t", "icon": "i"}}
    gs = {"group_reputation": 50}

    # F-16 (audit 2026-09-04): the clock arms from the first HOSTILE-ish tier
    # (index 2), not from "watchful" — a merely wary stakeholder is never
    # forced hostile on a timer.
    actions = [determine_npc_action("regulator", st, 55.0, gs, rnd, patience_limit=3)["action"]
               for rnd in range(1, 11)]
    assert actions == ["watchful"] * 10, actions   # ten rounds at watchful: nothing forced

    st2 = {"profile": st["profile"]}
    actions = [determine_npc_action("regulator", st2, 35.0, gs, rnd, patience_limit=3)["action"]
               for rnd in range(1, 6)]
    assert actions[0] == "watchful"                 # staged escalation: one step from a standing start
    assert actions[1] == "protest" and actions[2] == "protest"
    assert actions[3] == "legal"                    # 3 rounds at protest → forced escalation
    assert actions[4] == "protest"                  # clock reset after forcing

    determine_npc_action("regulator", st2, 90.0, gs, 6, patience_limit=3)  # cooperative
    assert st2["rounds_at_tier"] == 0 and st2["last_tier"] == 0


def test_stakeholder_intel_single_source_and_shape():
    """
    F6 §6.2/§6.4: the intel emitter is the single source of truth for demand /
    leverage / trend text, keeps raw scores off the player card, and every
    driver metric has a backend phrase (drift tripwire against the front-end).
    """
    from npc_stakeholders import (
        build_stakeholder_intel, create_initial_npc_state, NPC_PROFILES, _DEMAND_PHRASE,
    )

    # DRIFT TRIPWIRE: every satisfaction-driver metric must have a demand phrase,
    # so a card never renders a raw metric id and front/back can't diverge.
    used = {m for p in NPC_PROFILES.values() for (m, _, _) in p.get("satisfaction_drivers", [])}
    assert used <= set(_DEMAND_PHRASE), f"drivers without a demand phrase: {used - set(_DEMAND_PHRASE)}"

    st = create_initial_npc_state()
    gs = {"group_reputation": 40, "biodiversity_state": {}}
    bus = [{"bu_id": "b", "social_license_score": 30, "carbon_intensity": 70,
            "governance_risk_score": 60, "water_dependency": 50}]
    intel = build_stakeholder_intel(st, gs, bus)

    assert len(intel) == len(st["npcs"])
    for card in intel:
        assert card["demand"]                          # readable demand sentence
        assert card["leverage"]["label"]               # salience rendered in words
        assert card["trend"] in ("new", "improving", "declining", "steady")
        assert "satisfaction" not in card              # raw score NOT on the player card
        assert "satisfaction" in card["facilitator"]   # kept for the debrief view


def test_memory_on_populates_evolving_trust():
    """
    End-to-end: with `stakeholder_memory_enabled` ON, NPC `trust` is populated,
    diverges from the flat 50 seed, and evolves across rounds — proving the
    integrator is wired through process_tick → run_new_engines and that the
    carry-forward fix lets it persist.
    """
    overrides = dict(_PED_OVERRIDES)
    overrides["stakeholder_memory_enabled"] = True

    random.seed(_SEED)
    gs = _make_initial_global()
    bus = _make_initial_bus()
    trust_series: dict[str, list] = {}

    for rnd in range(1, 6):
        gs["round_number"] = rnd
        gs["pedagogical_overrides"] = dict(overrides)
        result = process_tick(
            current_global=copy.deepcopy(gs),
            current_bus=copy.deepcopy(bus),
            decisions=_decisions_for_round(rnd, bus),
            dividends_paid=500_000 if rnd > 1 else 0,
            crisis_severity=40.0,
            imitation_decay_rate=0.10,
            decision_paradigm="legacy_abc",
        )
        new_global, new_bus, events = result["global_state"], result["bu_states"], result["events"]
        new_global.setdefault("active_event_flags", {})["stochastic_seed"] = f"golden-{_SEED}"
        new_global["pedagogical_overrides"] = dict(overrides)
        run_new_engines(round_number=rnd, global_state=new_global, bu_states=new_bus, events=events)
        for k, v in (new_global.get("npc_stakeholders") or {}).get("npcs", {}).items():
            trust_series.setdefault(k, []).append(v.get("trust"))
        gs, bus = new_global, new_bus

    assert trust_series, "no NPC trust captured — memory wiring missing"
    all_vals = [t for series in trust_series.values() for t in series]
    assert all(isinstance(t, (int, float)) for t in all_vals), "trust must be numeric when memory on"
    assert any(len(set(series)) > 1 for series in trust_series.values()), "trust should evolve across rounds"
    assert any(t != 50.0 for t in all_vals), "trust should diverge from the 50 seed"


if __name__ == "__main__":
    trace = generate_trace()
    _write_golden(trace)
    print(f"Wrote golden trace ({len(trace)} rounds) to {_GOLDEN_PATH}")
    for row in trace:
        if "error" in row:
            print(f"  R{row['round']}: ERROR {row['error']}")
            continue
        avg_slo = sum(b["social_license_score"] for b in row["bus"]) / len(row["bus"])
        print(f"  R{row['round']:>2}: avg_SLO={avg_slo:6.2f}  rep={row['group_reputation']:6.2f}  "
              f"npcs={ {k: v['escalation_level'] for k, v in row['npcs'].items()} }")
