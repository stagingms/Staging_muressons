"""EVAL_Stakeholder_SLO recommendations 3-8 (owner ruling: implement all).

3. Named-NPC escalation is STAGED: a tier may worsen by at most one level per
   round (no more R1 proxy fights from a standing start).
4. SLO gets a recovery ramp and absolute-capex escapes: the natural-decay
   growth branch and the greenwash bar accept max(relative ratio, absolute
   capex), so the post-repair richer economy doesn't silently harden them.
5. The sentiment bridge runs at a low baseline weight even with F1 off, so
   the heat-map and NPC surfaces can never fully disagree.
6. Stakeholder-management side-track outcomes credit NPC trust / agent
   tolerance once (guarded), retiring their narrative-only taxonomy entries.
7. The regulator enforcement path survives states without corporate_treasury.
8. Cohort telemetry reports NPC tiers, agent triggers and negotiation deals.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "tests"))
os.environ.setdefault("USE_MEMORY_DB", "true")

from npc_stakeholders import create_initial_npc_state, process_npc_tick  # noqa: E402


def _bad_gs(rnd):
    return {"group_reputation": 25, "corporate_treasury": 50e6,
            "round_number": rnd,
            "active_event_flags": {"stochastic_seed": "recs-probe"}}


_BAD_BUS = [{"social_license_score": 20, "carbon_intensity": 80,
             "governance_risk_score": 60}]


def _tier_of(state, npc_id):
    st = state["npcs"][npc_id]
    levels = st["profile"]["escalation_levels"]
    for i, lvl in enumerate(levels):
        if lvl["action"] == st.get("escalation_level"):
            return i
    return None


# ── 3. staged escalation ───────────────────────────────────────────────────

def test_npc_escalation_walks_one_tier_per_round():
    state = create_initial_npc_state()
    tiers = []
    for rnd in range(1, 5):
        state, _ = process_npc_tick(state, _bad_gs(rnd), list(_BAD_BUS), {}, rnd,
                                    memory_enabled=False)
        tiers.append(_tier_of(state, "activist_investor"))
    # R1 from a standing start may reach at most one step past cooperative
    assert tiers[0] is not None and tiers[0] <= 1, (
        f"R1 jumped straight to tier {tiers[0]} — escalation is not staged")
    for a, b in zip(tiers, tiers[1:]):
        assert b <= a + 1, f"tier jumped {a}→{b} in one round"
    # and sustained bad KPIs do eventually reach the top tier
    assert tiers[-1] >= len(state["npcs"]["activist_investor"]["profile"]["escalation_levels"]) - 1


def test_npc_deescalation_is_not_rate_limited():
    state = create_initial_npc_state()
    for rnd in range(1, 5):
        state, _ = process_npc_tick(state, _bad_gs(rnd), list(_BAD_BUS), {}, rnd,
                                    memory_enabled=False)
    deep = _tier_of(state, "activist_investor")
    good_gs = {"group_reputation": 80, "corporate_treasury": 50e6, "round_number": 5,
               "active_event_flags": {"stochastic_seed": "recs-probe"}}
    good_bus = [{"social_license_score": 85, "carbon_intensity": 20,
                 "governance_risk_score": 5}]
    state, _ = process_npc_tick(state, good_gs, good_bus, {}, 5, memory_enabled=False)
    assert _tier_of(state, "activist_investor") < deep


# ── 4. SLO ramp + absolute escapes ─────────────────────────────────────────

def test_natural_decay_growth_branch_has_an_absolute_capex_escape():
    from engine import apply_natural_decay
    from config import NATURAL_DECAY_GROWTH_ABS_CAPEX
    rep, slo = apply_natural_decay(50.0, 40.0, True, investment_ratio=0.05,
                                   capex_abs=NATURAL_DECAY_GROWTH_ABS_CAPEX)
    assert slo > 40.0, "absolute capex at the growth floor must grow SLO"


def test_natural_decay_has_a_mild_middle_growth_tier():
    from engine import apply_natural_decay
    _, slo = apply_natural_decay(50.0, 40.0, True, investment_ratio=0.22)
    assert 40.0 < slo < 43.5, f"ratio 0.22 should grow SLO mildly, got {slo}"


def test_greenwash_bar_accepts_absolute_capex():
    from engine import calc_greenwashing_risk
    from config import GREENWASH_ABS_CAPEX_FLOOR
    decisions = [{"investment_ratio": 0.02, "capex_allocated": GREENWASH_ABS_CAPEX_FLOOR}
                 for _ in range(4)]
    hit, pen = calc_greenwashing_risk("option_a", decisions, claim_level="full")
    assert hit is False, "absolute capex at the floor must satisfy a green claim"
    lazy = [{"investment_ratio": 0.02, "capex_allocated": 100_000} for _ in range(4)]
    hit2, _ = calc_greenwashing_risk("option_a", lazy, claim_level="full")
    assert hit2 is True, "tiny capex with a tiny ratio must still be greenwash"


# ── 5. always-on low-weight sentiment bridge ───────────────────────────────

def test_sentiment_bridge_applies_at_baseline_weight_without_memory():
    state = create_initial_npc_state()
    gs = _bad_gs(1)
    gs["active_event_flags"]["sentiment_stakeholders"] = [
        {"id": "activist_investor_grp", "attitude_score": 90.0},
    ]
    state, diag = process_npc_tick(state, gs, list(_BAD_BUS), {}, 1,
                                   memory_enabled=False)
    # the same KPIs WITHOUT the sentiment list produce a lower satisfaction —
    # the bridge must have pulled toward the 90 attitude even with F1 off
    state2 = create_initial_npc_state()
    state2, diag2 = process_npc_tick(state2, _bad_gs(1), list(_BAD_BUS), {}, 1,
                                     memory_enabled=False)
    sat_bridged = next(a["satisfaction"] for a in diag["npc_actions"]
                       if a["npc_id"] == "activist_investor")
    sat_plain = next(a["satisfaction"] for a in diag2["npc_actions"]
                     if a["npc_id"] == "activist_investor")
    assert sat_bridged > sat_plain, "baseline bridge did not pull toward sentiment"


# ── 6. sm side-track outcomes credit trust / tolerance once ────────────────

def test_sm_track_outcomes_credit_stakeholders_once():
    from npc_stakeholders import apply_sm_track_credits, SM_TRACK_CREDITS
    from autonomous_agents import create_initial_agent_state
    assert "sm_esg_gold_standard" in SM_TRACK_CREDITS
    npc = create_initial_npc_state()
    for st in npc["npcs"].values():           # give the trust stock something to move
        st["trust"] = 50.0
        st["trust_initialised"] = True
    agents = create_initial_agent_state()
    flags = {"sm_esg_gold_standard": True, "sm_media_hostile": True}
    diag = apply_sm_track_credits(npc, agents, flags)
    assert diag["applied"], "credits did not apply"
    assert flags.get("sm_stakeholder_credits_applied"), "guard flag not stamped"
    assert npc["npcs"]["activist_investor"]["trust"] > 50.0
    assert npc["npcs"]["journalist"]["trust"] < 50.0 + SM_TRACK_CREDITS["sm_esg_gold_standard"]["trust"], \
        "sm_media_hostile debit did not land on the journalist"
    # second application is a no-op
    before = npc["npcs"]["activist_investor"]["trust"]
    diag2 = apply_sm_track_credits(npc, agents, flags)
    assert not diag2["applied"]
    assert npc["npcs"]["activist_investor"]["trust"] == before


# ── 7. treasury guard ──────────────────────────────────────────────────────

def test_enforcement_survives_state_without_treasury():
    state = create_initial_npc_state()
    gs = {"group_reputation": 25, "round_number": 2,
          "active_event_flags": {"stochastic_seed": "probe"}}
    for rnd in range(1, 4):   # walk deep enough to hit enforcement tiers
        gs["round_number"] = rnd
        state, _ = process_npc_tick(state, gs, list(_BAD_BUS), {}, rnd,
                                    memory_enabled=True)
    # reaching here without KeyError is the assertion


# ── 8. telemetry extension ─────────────────────────────────────────────────

def test_telemetry_reports_stakeholder_surface():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_ct", BACKEND.parent / "scripts" / "cohort_telemetry.py")
    CT = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(CT)
    hist = []
    for n in range(1, 11):
        gs = {"corporate_treasury": 1e6,
              "active_event_flags": {} if n < 10 else {
                  "terminal_value": 1.0, "regenerative_multiple": 1.0,
                  "archetype": "X", "mr_breakdown": {"base": 1.0},
                  "negotiation_log": {"active": None, "history": [
                      {"round": 4, "agent_id": "the_regulator", "status": "closed",
                       "deals": [{"concession_id": "governance_audit"}]},
                      {"round": 6, "agent_id": "the_journalist", "status": "closed",
                       "deals": []},
                  ]},
              },
              "npc_stakeholders": {"npcs": {"activist_investor": {
                  "escalation_level": "hostile" if n >= 5 else "concerned",
                  "profile": {"escalation_levels": [
                      {"action": "supportive"}, {"action": "concerned"},
                      {"action": "hostile"}, {"action": "adversarial"}]}}}},
              "autonomous_agents": {"agents": {"the_regulator": {
                  "escalation_stage": "triggered" if n >= 8 else "agitated",
                  "triggered_round": 8 if n >= 8 else None}}},
              }
        hist.append({"round_number": n, "global_state": gs,
                     "business_units": [], "decisions": []})
    t = CT.summarize_team(hist)
    assert t["npc_worst_tiers"].get("activist_investor") == 2
    assert t["agents_triggered"] == ["the_regulator"]
    assert t["negotiation_deals"] == 1
    assert t["negotiation_meetings"] == 2
