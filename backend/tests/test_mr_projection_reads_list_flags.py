"""Mid-game M_R projections read the flags the finale reads — audit
2026-09-04 F-15 · WP-14.

The finale builds calculate_mr's input through collect_all_flags, which
expands the `rN_flags` lists where the option layer stores every strategic
flag (`r7_flags: ["synergy_unlock"]`, top-level `synergy_unlock: None`). The
engine's valuation preview, the Consequence-DNA projection and the What-If
replay handed calculate_mr the RAW dict, so those flags were invisible:
370 of 384 probed states diverged from the award (up to −0.57), and the
preview also GRANTED the resilience bonus to a team whose `insurance_only`
lived in a list. One helper — flag_utils.mr_input_from_state — now feeds
all of them.
"""
from __future__ import annotations

import asyncio
import copy
import os
import random
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET", "testsecret0123456789abcdefabcdef")

from flag_utils import collect_all_flags, hr_investment_rounds_from, mr_flags_from, mr_input_from_state  # noqa: E402
from terminal_valuation import calculate_mr  # noqa: E402

# A state the way production stores it: strategic flags inside per-round lists,
# their top-level keys absent or None, HR investment as hr_invested_r{N}.
_LIST_FLAGS = {
    "stochastic_seed": "f15",
    "r2_flags": ["materiality_aligned"],
    "r6_flags": ["ethical_ai_overhaul", "ai_monetised"],
    "r7_flags": ["synergy_unlock", "waste_to_energy"],
    "r9_flags": ["community_fund"],
    "synergy_unlock": None,
    "hr_invested_r3": True,
    "hr_invested_r8": True,
}
_KPIS = dict(avg_slo=80.0, avg_burnout=10.0, workforce_readiness=50.0, synergy_multiplier=1.0)


# ── the helper ─────────────────────────────────────────────────────────────

def test_mr_flags_from_expands_the_lists_the_finale_expands():
    names = collect_all_flags(_LIST_FLAGS)
    for f in ("materiality_aligned", "ethical_ai_overhaul", "synergy_unlock", "community_fund"):
        assert f in names
    mrf = mr_flags_from(_LIST_FLAGS)
    assert mrf["synergy_unlock"] is True and mrf["community_fund"] is True
    assert hr_investment_rounds_from(_LIST_FLAGS) == 2
    flags, hr = mr_input_from_state({"active_event_flags": _LIST_FLAGS}, {"r10_flags": ["resist_integrate"], "_private": 1})
    assert flags.get("resist_integrate") is True and hr == 2
    assert "_private" not in flags


def test_the_numeric_brsr_dividend_keeps_its_value():
    flags = mr_flags_from({"brsr_net_positive_dividend": 0.05, "r1_flags": ["brsr_pioneer"]})
    assert flags["brsr_net_positive_dividend"] == 0.05 and flags["brsr_pioneer"] is True
    assert "brsr_net_positive_dividend" not in mr_flags_from({"brsr_net_positive_dividend": 0})


def test_the_raw_dict_and_the_expanded_flags_price_differently():
    """The defect, stated as a number: on this state the raw dict misses
    +0.10 +0.15 +0.15 +0.18×JT of M_R."""
    raw = calculate_mr(_LIST_FLAGS, hr_investment_rounds=0, **_KPIS)["mr"]
    expanded = calculate_mr(mr_flags_from(_LIST_FLAGS), hr_investment_rounds=2, **_KPIS)["mr"]
    assert expanded - raw >= 0.55, f"raw {raw} vs expanded {expanded}"


# ── the engine preview ─────────────────────────────────────────────────────

def test_engine_preview_equals_the_arbiter_on_expanded_flags():
    from tests.test_launch_audit_2026_09_01 import _tick_state, _tick
    gs, bus = _tick_state(round_number=9)
    gs["active_event_flags"] = dict(_LIST_FLAGS)
    gs["workforce_readiness"] = 50.0
    for b in bus:
        b["social_license_score"] = 80.0
        b["staff_burnout_index"] = 10.0
    res = _tick(gs, bus, capex=1, ratio=0.3)
    pv = res["events"]["valuation_preview"]
    new_bus = res["bu_states"]
    n = len(new_bus)
    # process_tick rebuilds active_event_flags from this tick's events (the
    # router merges the previous flags afterwards), so the preview's input is
    # the ENTERING state plus the tick's events — exactly what it saw.
    mr_flags, hr = mr_input_from_state(gs, res["events"])
    expected = calculate_mr(
        mr_flags,
        sum(b.get("social_license_score", 50) for b in new_bus) / n,
        sum(b.get("staff_burnout_index", 0) for b in new_bus) / n,
        50.0, float(res["global_state"].get("synergy_multiplier", 0.0)), hr,
    )["mr"]
    assert pv["mr_projection"] == pytest.approx(expected, abs=1e-4)
    assert hr == 2
    # and it is NOT the raw-dict figure
    raw = calculate_mr(
        {**gs["active_event_flags"], **{k: v for k, v in res["events"].items() if not k.startswith("_")}},
        sum(b.get("social_license_score", 50) for b in new_bus) / n,
        sum(b.get("staff_burnout_index", 0) for b in new_bus) / n,
        50.0, float(res["global_state"].get("synergy_multiplier", 0.0)), 0,
    )["mr"]
    assert pv["mr_projection"] > raw + 0.3


def test_preview_does_not_grant_resilience_a_listed_insurance_only_blocks():
    from tests.test_launch_audit_2026_09_01 import _tick_state, _tick
    gs, bus = _tick_state(round_number=6)
    gs["active_event_flags"] = {"stochastic_seed": "f15b", "r5_flags": ["insurance_only"]}
    res = _tick(gs, bus, capex=1, ratio=0.3)
    mr_flags, hr = mr_input_from_state(gs, res["events"])
    assert mr_flags.get("insurance_only") is True
    bd = calculate_mr(mr_flags, 55.0, 15.0, 50.0, 0.35, hr)["breakdown"]
    assert "resilience_bonus" not in bd
    n = len(res["bu_states"])
    expected = calculate_mr(
        mr_flags,
        sum(b.get("social_license_score", 50) for b in res["bu_states"]) / n,
        sum(b.get("staff_burnout_index", 0) for b in res["bu_states"]) / n,
        50.0, float(res["global_state"].get("synergy_multiplier", 0.0)), hr,
    )["mr"]
    assert res["events"]["valuation_preview"]["mr_projection"] == pytest.approx(expected, abs=1e-4)


# ── the finale, on the same state ──────────────────────────────────────────

def _mk_bus(slo=80.0, burnout=10.0):
    return [{"bu_id": b, "revenue_base": 12_000_000.0, "opex_base": 8_000_000.0,
             "carbon_intensity": 10.0, "social_license_score": slo,
             "governance_risk_score": 20.0, "natural_capital_debt": 10.0,
             "water_dependency": 30.0, "staff_burnout_index": burnout,
             "bed_capacity_utilization": 0.5, "talent_penalty": 0}
            for b in ("energy", "electronics", "agri", "software", "pharma")]


def test_finale_award_equals_the_arbiter_on_list_held_flags():
    """tests/test_mr_single_arbiter pins the equality with `{}` flags, which
    cannot see this bug; this is the same pin on a real flag layout."""
    from round_logic import post_tick
    random.seed(11)
    bus = _mk_bus()
    gs = {"corporate_treasury": 100_000_000.0, "group_reputation": 70.0,
          "green_transition_fund": 0.0, "synergy_multiplier": 1.0,
          "round_number": 10, "active_event_flags": dict(_LIST_FLAGS),
          "workforce_readiness": 50.0, "climate_resilience": 0.5,
          "session_id": "", "cost_of_capital": 0.08}
    prev_flags = copy.deepcopy(_LIST_FLAGS)
    decs = [{"choice_selected": "option_b", "capex_allocated": 0, "investment_ratio": 0.4, "bu_id": b["bu_id"]} for b in bus]
    extra = post_tick(10, gs, bus, decs, {}, prev_flags)
    bd = extra["mr_breakdown"]
    assert bd.get("synergy_bonus", 0) > 0 and bd.get("truth_premium") == 0.15 and bd.get("community_champion_bonus", 0) > 0.18
    assert extra["mr_jt_hr_rounds"] == 2


# ── the DNA projection and the What-If replay ──────────────────────────────

def test_dna_projection_reads_the_expanded_flags():
    from consequence_dna_api import build_consequence_dna_data
    gs = {"corporate_treasury": 60_000_000.0, "group_reputation": 65.0, "synergy_multiplier": 1.0,
          "round_number": 8, "workforce_readiness": 50.0, "active_event_flags": dict(_LIST_FLAGS)}
    bus = _mk_bus()
    data = build_consequence_dna_data(session_id="s", global_state=gs, bu_states=bus, history=[])
    nodes = {n["id"]: n for n in data.get("nodes", []) if isinstance(n, dict)} if isinstance(data.get("nodes"), list) else {}
    proj = {k: v for k, v in nodes.items() if k.startswith("proj_")} if nodes else {}
    if not proj:  # nodes may be nested; fall back to the projection dict
        text = str(data)
        assert "synergy_bonus" in text and "truth_premium" in text
    else:
        assert "proj_synergy_bonus" in proj and "proj_truth_premium" in proj


def test_what_if_replay_reads_the_expanded_flags_and_the_dynamic_multiple():
    import httpx
    from httpx import ASGITransport
    import database as db
    import admin_shared
    import master_credentials
    from main import app
    master_credentials.MASTER_PASSWORD = "test-master-pw"
    master_credentials._load_override_hash = lambda: None
    admin_shared._god_mode_settings["solo_mode_enabled"] = True

    async def go():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
            r = await ac.post("/api/simulations/solo-start", json={"player_name": "WhatIf", "decision_paradigm": "legacy_abc"})
            sid = r.json()["session_id"]
            latest = await db.fetch_latest_state(sid)
            gs = latest["global_state"]
            gs["active_event_flags"] = {**gs.get("active_event_flags", {}), **_LIST_FLAGS}
            await db.update_latest_global_state(sid, gs, latest["bu_states"])
            assert (await ac.post("/api/admin/facilitators/login",
                                  json={"facilitator_id": "god_mode", "password": "test-master-pw"})).status_code == 200
            r = await ac.post(f"/api/admin/what-if/{sid}", json={"flag_overrides": {"synergy_unlock": False}})
            assert r.status_code == 200, r.text[:200]
            return r.json()
    loop = asyncio.new_event_loop()
    try:
        out = loop.run_until_complete(go())
    finally:
        loop.close()
    base = out["baseline"]["mr_breakdown"]
    assert base.get("truth_premium") == 0.15 and base.get("community_champion_bonus", 0) > 0.18, base
    assert base.get("synergy_bonus", 0) > 0
    assert out["what_if"]["mr_breakdown"].get("synergy_bonus", 0) == 0, "the override did not remove the listed flag"
    # dynamic multiple, not a fixed 12×: the handler passes use_dynamic_multiple
    import inspect
    import admin_router
    src = inspect.getsource(admin_router.what_if_replay)
    assert "use_dynamic_multiple=True" in src and "mr_input_from_state(gs)" in src
