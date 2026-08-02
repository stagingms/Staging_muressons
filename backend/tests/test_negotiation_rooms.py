"""Negotiation Rooms Phase 1 — deal engine tests.

Covers (SPEC §10): state-machine transitions, offer-validation matrix,
tolerance-cap math at the watching threshold, repeat/scar pricing, promise
tagging + shared-ledger resolution, walk-out memory, meeting caps, and
auto-close-on-commit.
"""
import copy

import pytest

from negotiation import (
    CONCESSION_CATALOG, MEETING_FEE, MAX_MEETINGS_PER_ROUND, MAX_TURNS,
    open_room, say, accept_concession, walk_out, close_on_commit,
    priced_cost, get_negotiation_log, compute_grievances, menu_for_agent,
)
from autonomous_agents import AGENT_PROFILES, create_initial_agent_state, resolve_agent_promises


def _gs(stage="hostile", agent="the_regulator", treasury=50_000_000):
    gs = {
        "round_number": 4,
        "corporate_treasury": treasury,
        "group_reputation": 40.0,
        "active_event_flags": {},
        "autonomous_agents": create_initial_agent_state(),
    }
    st = gs["autonomous_agents"]["agents"][agent]
    st["escalation_stage"] = stage
    st["tolerance"] = 18.0   # deep in hostile territory
    return gs


def _bus():
    return [
        {"bu_id": "pharma", "revenue_base": 18e6, "opex_base": 11e6,
         "governance_risk_score": 75.0, "social_license_score": 40.0,
         "carbon_intensity": 80.0, "staff_burnout_index": 30.0,
         "natural_capital_debt": 20.0},
        {"bu_id": "software", "revenue_base": 8e6, "opex_base": 4e6,
         "governance_risk_score": 50.0, "social_license_score": 45.0,
         "carbon_intensity": 30.0, "staff_burnout_index": 20.0,
         "natural_capital_debt": 5.0},
    ]


# ── Opening ─────────────────────────────────────────────────────────────────

def test_open_requires_hostile():
    gs = _gs(stage="agitated")
    r = open_room(gs, _bus(), 4, "the_regulator")
    assert r["error"] == "not_hostile" and r["stage"] == "agitated"


def test_open_charges_fee_and_seeds_persona_and_grievances():
    gs = _gs()
    t0 = gs["corporate_treasury"]
    r = open_room(gs, _bus(), 4, "the_regulator")
    assert "room" in r
    assert gs["corporate_treasury"] == t0 - MEETING_FEE
    room = r["room"]
    assert room["persona"]["name"] == "Commissioner Carson"
    # grievances computed from engine truth: gov 55-line breached (avg 55? 60/50→55)
    breached = [g for g in room["grievances"] if g["breached"]]
    assert breached, room["grievances"]
    # opening line is in persona voice and cites the top grievance
    assert room["turns"][0]["who"] == "agent"


def test_only_one_room_and_round_cap():
    gs = _gs()
    assert "room" in open_room(gs, _bus(), 4, "the_regulator")
    r2 = open_room(gs, _bus(), 4, "the_regulator")
    assert r2["error"] == "room_already_open"
    walk_out(gs, 4)
    # 2nd meeting this round ok, 3rd blocked
    gs["autonomous_agents"]["agents"]["the_journalist"]["escalation_stage"] = "hostile"
    assert "room" in open_room(gs, _bus(), 4, "the_journalist")
    walk_out(gs, 4)
    r3 = open_room(gs, _bus(), 4, "the_regulator")
    assert r3["error"] == "meeting_cap_reached"


def test_unknown_agent_and_inactive_state():
    gs = _gs()
    assert open_room(gs, _bus(), 4, "the_easter_bunny")["error"] == "unknown_agent"
    gs2 = {"round_number": 4, "corporate_treasury": 1, "active_event_flags": {}}
    assert open_room(gs2, _bus(), 4, "the_regulator")["error"] == "agents_not_active"


# ── Offer validation matrix ────────────────────────────────────────────────

def test_accept_validation_matrix():
    gs = _gs()
    open_room(gs, _bus(), 4, "the_regulator")
    assert accept_concession(gs, _bus(), 4, "flux_capacitor")["error"] == "unknown_concession"
    # journalist-only item refused on the regulator's menu
    assert accept_concession(gs, _bus(), 4, "transparency_pact")["error"] == "not_on_this_agents_menu"
    # one promised concession per meeting
    assert "deal" in accept_concession(gs, _bus(), 4, "remediation_fund")
    assert accept_concession(gs, _bus(), 4, "governance_audit")["error"] == "one_promised_concession_per_meeting"
    # one free action per meeting
    assert "deal" in accept_concession(gs, _bus(), 4, "public_apology")
    assert accept_concession(gs, _bus(), 4, "public_apology")["error"] == "one_free_action_per_meeting"


def test_no_room_no_deal():
    gs = _gs()
    assert accept_concession(gs, _bus(), 4, "remediation_fund")["error"] == "no_open_room"
    assert say(gs, _bus(), 4, "hello?")["error"] == "no_open_room"
    assert walk_out(gs, 4)["error"] == "no_open_room"


# ── Tolerance cap + effects ────────────────────────────────────────────────

def test_tolerance_capped_at_watching_threshold():
    gs = _gs()
    open_room(gs, _bus(), 4, "the_regulator")
    st = gs["autonomous_agents"]["agents"]["the_regulator"]
    st["tolerance"] = 60.0  # near the cap (watching = 65)
    r = accept_concession(gs, _bus(), 4, "remediation_fund")  # +12 would be 72
    cap = AGENT_PROFILES["the_regulator"]["escalation_thresholds"]["watching"]
    assert r["deal"]["tolerance_after"] == cap == 65


def test_apology_costs_reputation_not_money():
    gs = _gs()
    open_room(gs, _bus(), 4, "the_regulator")
    t0, rep0 = gs["corporate_treasury"], gs["group_reputation"]
    r = accept_concession(gs, _bus(), 4, "public_apology")
    assert gs["corporate_treasury"] == t0          # free tier
    assert gs["group_reputation"] == rep0 - 2.0    # humble pie
    assert r["promise"] is None


# ── Pricing: repeat ladder + scar surcharge ────────────────────────────────

def test_repeat_pricing_ladder_and_scar():
    gs = _gs()
    bus = _bus()
    assert priced_cost(gs, 4, "the_regulator", "remediation_fund")["multiplier"] == 1.0
    open_room(gs, bus, 4, "the_regulator")
    accept_concession(gs, bus, 4, "remediation_fund")
    assert priced_cost(gs, 4, "the_regulator", "remediation_fund")["multiplier"] == 1.5
    walk_out(gs, 4)
    gs["autonomous_agents"]["agents"]["the_regulator"]["escalation_stage"] = "hostile"
    open_room(gs, bus, 4, "the_regulator")
    accept_concession(gs, bus, 4, "governance_audit")
    assert priced_cost(gs, 4, "the_regulator", "remediation_fund")["multiplier"] == 2.0
    # live scar adds 25%
    gs["autonomous_agents"]["agents"]["the_regulator"]["scar_until"] = 9
    assert priced_cost(gs, 4, "the_regulator", "remediation_fund")["multiplier"] == 2.25


# ── Promises: shared F5 ledger ─────────────────────────────────────────────

def test_promise_registered_tagged_and_resolvable():
    gs = _gs()
    bus = _bus()
    open_room(gs, bus, 4, "the_regulator")
    r = accept_concession(gs, bus, 4, "remediation_fund")
    p = r["promise"]
    assert p["source"] == "negotiation" and p["metric"] == "avg_slo"
    assert p["due_round"] == 6
    ledger = gs["autonomous_agents"]["promises"]
    assert ledger and ledger[0]["id"] == p["id"]
    # kept: raise SLO above target, resolve at due round via the F5 resolver
    for b in bus:
        b["social_license_score"] = p["target"] + 10
    out = resolve_agent_promises(gs["autonomous_agents"], gs, bus, 6)
    assert out and out[0]["state"] == "kept"


def test_broken_negotiated_promise_scars():
    gs = _gs()
    bus = _bus()
    open_room(gs, bus, 4, "the_regulator")
    r = accept_concession(gs, bus, 4, "remediation_fund")
    p = r["promise"]
    for b in bus:
        b["social_license_score"] = p["target"] - 20  # miss it
    out = resolve_agent_promises(gs["autonomous_agents"], gs, bus, 6)
    assert out and out[0]["state"] == "broken"
    assert gs["autonomous_agents"]["agents"]["the_regulator"]["scar_until"] > 6


# ── Dialogue + closure ─────────────────────────────────────────────────────

def test_turn_limit_closes_room():
    gs = _gs()
    bus = _bus()
    open_room(gs, bus, 4, "the_regulator")
    for i in range(MAX_TURNS):
        r = say(gs, bus, 4, f"turn {i}")
        assert "room" in r
    r = say(gs, bus, 4, "one too many")
    assert "closed" in r and r["closed"]["resolution"] == "turn_limit"


def test_walk_out_without_deal_costs_patience():
    gs = _gs()
    open_room(gs, _bus(), 4, "the_regulator")
    st = gs["autonomous_agents"]["agents"]["the_regulator"]
    p0 = st.get("patience_counter", 0)
    r = walk_out(gs, 4)
    assert r["closed"]["resolution"] == "walk_out"
    assert st["patience_counter"] == p0 + 1
    assert get_negotiation_log(gs)["active"] is None
    assert get_negotiation_log(gs)["history"][-1]["resolution"] == "walk_out"


def test_close_on_commit_and_dual_representation():
    gs = _gs()
    open_room(gs, _bus(), 4, "the_regulator")
    closed = close_on_commit(gs, 4)
    assert closed and closed["resolution"] == "round_committed"
    log = get_negotiation_log(gs)
    assert log["active"] is None
    # dual representation: same object in flags and top level (parity pattern)
    assert gs["active_event_flags"]["negotiation_log"] is gs["negotiation_log"]
    assert close_on_commit(gs, 4) is None  # idempotent


def test_menu_is_per_agent():
    gs = _gs()
    ids_reg = {m["id"] for m in menu_for_agent(gs, 4, "the_regulator")}
    ids_journo = {m["id"] for m in menu_for_agent(gs, 4, "the_journalist")}
    assert "transparency_pact" not in ids_reg
    assert "transparency_pact" in ids_journo
    assert "public_apology" in ids_reg and "public_apology" in ids_journo
