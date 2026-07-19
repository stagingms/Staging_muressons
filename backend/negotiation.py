"""
negotiation.py — Stakeholder Negotiation Rooms, Phase 1: the deal engine.
(SPEC_Stakeholder_Negotiation_Rooms.md §4–§6, scripted fallback mode.)

Design rules enforced HERE, not in any client or LLM:
  • Concessions come from an enumerated whitelist with per-agent availability
    derived from what each persona monitors — validation is server-side and
    total (unknown id, wrong agent, over caps → refused).
  • De-escalation is bought in TOLERANCE and capped at the agent's `watching`
    threshold: a deal buys you out of a fire, never into being loved. The
    road back to dormant stays clean rounds only (recovery_rate).
  • Deals above the free tier register on the SAME F5 promise ledger that
    `resolve_agent_promises` judges (tagged source="negotiation"), so kept
    promises pay and broken promises scar through the existing machinery.
  • Repeat deals with the same agent get more expensive (×1.5, ×2 cap) and a
    live trust scar adds a 25% surcharge — reputation is a repeated game.
  • Everything is pure state-in/state-out on the session's global state; the
    engine tick is never touched. Bounded, auditable, deterministic.

Room state lives at active_event_flags.negotiation_log with the SAME
dual-representation persistence pattern as predictions_log (memory-store
pack/unpack parity — see router.submit_prediction).
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Optional

from autonomous_agents import AGENT_PROFILES, _compute_agent_metrics

# ── Tunables (Phase 1 constants; config-Excel routing can follow the
#    stakeholder_engagement._engagement_consts pattern later) ────────────────
MEETING_FEE = 250_000          # charged on entry, win or lose
MAX_MEETINGS_PER_ROUND = 2     # per team
MAX_TURNS = 6                  # dialogue turns per room
REPEAT_PRICE_LADDER = (1.0, 1.5, 2.0)   # 1st/2nd/3rd+ accepted deal per agent
SCAR_SURCHARGE = 0.25          # +25% while a broken-promise scar is live
PROMISE_HORIZON = 2            # rounds until a negotiated promise comes due

# ── Concession whitelist (SPEC §4) ──────────────────────────────────────────
# NOTE v1 resolver constraint: resolve_agent_promises judges kept as
# value >= target, so promises here only use ">="-directional metrics
# (avg_slo, group_reputation). Inverted metrics (governance risk, burnout)
# get their relief as bounded IMMEDIATE effects instead.
CONCESSION_CATALOG: dict[str, dict] = {
    "remediation_fund": {
        "label": "Community Remediation Fund",
        "agents": ("the_regulator", "the_community_activist"),
        "cost": 2_000_000, "tolerance": 12,
        "promise": {"metric": "avg_slo", "target_bump": 5.0},
        "effects": {},
    },
    "governance_audit": {
        "label": "Independent Governance Audit",
        "agents": ("the_regulator", "the_institutional_investor"),
        "cost": 1_500_000, "tolerance": 10,
        # gov relief is immediate (resolver can't judge <=-metrics, see NOTE)
        "promise": {"metric": "group_reputation", "target_bump": 3.0},
        "effects": {"governance_risk_delta": -3.0},
    },
    "transparency_pact": {
        "label": "Radical Transparency Pact",
        "agents": ("the_journalist",),
        "cost": 500_000, "tolerance": 8,
        "promise": {"metric": "group_reputation", "target_bump": 2.0},
        "effects": {"flag": ("radical_transparency_pact", 2)},  # flag, rounds
    },
    "wellbeing_program": {
        "label": "Workforce Wellbeing Program",
        "agents": ("the_gen_z_employee",),
        "cost": 1_000_000, "tolerance": 10,
        "promise": {"metric": "avg_slo", "target_bump": 3.0},
        "effects": {"burnout_delta": -4.0},
    },
    "dividend_signal": {
        "label": "Dividend Commitment Signal",
        "agents": ("the_institutional_investor",),
        "cost": 500_000, "tolerance": 8,
        "promise": {"metric": "group_reputation", "target_bump": 2.0},
        "effects": {},
    },
    "public_apology": {
        "label": "Public Apology",
        "agents": tuple(AGENT_PROFILES.keys()),
        "cost": 0, "tolerance": 4,
        "promise": None,                       # free tier: no promise
        "effects": {"reputation_delta": -2.0}, # humble pie has a price
    },
}


# ── Helpers ─────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_negotiation_log(gs: dict) -> dict:
    flags = gs.setdefault("active_event_flags", {})
    log = gs.get("negotiation_log") or flags.get("negotiation_log")
    if not isinstance(log, dict):
        log = {"active": None, "history": []}
    # dual representation (parity pattern)
    flags["negotiation_log"] = log
    gs["negotiation_log"] = log
    return log


def _agent_state(gs: dict, agent_id: str) -> Optional[dict]:
    return ((gs.get("autonomous_agents") or {}).get("agents") or {}).get(agent_id)


def compute_grievances(gs: dict, bus: list[dict], agent_id: str) -> list[dict]:
    """The agent's grievance list: engine truth vs their red lines — computed,
    never hallucinated (SPEC §2)."""
    profile = AGENT_PROFILES.get(agent_id) or {}
    metrics = _compute_agent_metrics(gs, bus)
    out = []
    for m in profile.get("monitored_metrics", []):
        cur = metrics.get(m["key"])
        if cur is None:
            continue
        breached = (cur > m["red_line"]) if m["direction"] == "above" else (cur < m["red_line"])
        out.append({
            "metric": m["key"], "current": round(float(cur), 1),
            "red_line": m["red_line"], "direction": m["direction"],
            "breached": bool(breached), "weight": m["weight"],
        })
    return sorted(out, key=lambda g: (not g["breached"], -g["weight"]))


def menu_for_agent(gs: dict, round_number: int, agent_id: str) -> list[dict]:
    """The agent's concession menu with LIVE prices (repeat ladder + scar)."""
    out = []
    for cid, spec in CONCESSION_CATALOG.items():
        if agent_id not in spec["agents"]:
            continue
        price = priced_cost(gs, round_number, agent_id, cid)
        out.append({
            "id": cid, "label": spec["label"], "cost": price["cost"],
            "base_cost": spec["cost"], "multiplier": price["multiplier"],
            "tolerance_gain": spec["tolerance"],
            "creates_promise": bool(spec["promise"]),
            "promise_metric": (spec["promise"] or {}).get("metric"),
            "effects": {k: v for k, v in spec["effects"].items()},
        })
    return out


def _prior_deals_with(gs: dict, agent_id: str) -> int:
    log = get_negotiation_log(gs)
    n = 0
    for room in log.get("history", []):
        n += sum(1 for d in room.get("deals", []) if room.get("agent_id") == agent_id and d)
    active = log.get("active")
    if active and active.get("agent_id") == agent_id:
        n += len(active.get("deals", []))
    return n


def priced_cost(gs: dict, round_number: int, agent_id: str, concession_id: str) -> dict:
    spec = CONCESSION_CATALOG[concession_id]
    n = _prior_deals_with(gs, agent_id)
    mult = REPEAT_PRICE_LADDER[min(n, len(REPEAT_PRICE_LADDER) - 1)]
    st = _agent_state(gs, agent_id) or {}
    scar = int(st.get("scar_until") or 0) > int(round_number)
    if scar:
        mult += SCAR_SURCHARGE
    return {"cost": round(spec["cost"] * mult, 2), "multiplier": mult, "scarred": scar}


def _meetings_this_round(gs: dict, round_number: int) -> int:
    log = get_negotiation_log(gs)
    n = sum(1 for r in log.get("history", []) if r.get("round") == round_number)
    if log.get("active"):
        n += 1
    return n


def scripted_line(agent_id: str, stage: str, grievances: list[dict], turn: int) -> str:
    """Deterministic persona voice for fallback mode (Phase 1 is fallback-only).
    Uses the profile's authored stage_dialogue plus the top computed grievance."""
    profile = AGENT_PROFILES.get(agent_id) or {}
    base = (profile.get("stage_dialogue") or {}).get(stage) or \
        f"{profile.get('name', agent_id)} regards you in silence."
    top = next((g for g in grievances if g["breached"]), None)
    if top is None:
        return base
    want = "below" if top["direction"] == "above" else "above"
    ask = (f" '{profile.get('name', 'They')} will consider de-escalation when "
           f"{top['metric'].replace('_', ' ')} is {want} {top['red_line']} — "
           f"today it stands at {top['current']}.'")
    if turn == 0:
        return base + ask
    return (f"{profile.get('name', 'They')}: 'Talk is not a concession. "
            f"My position on {top['metric'].replace('_', ' ')} has not moved.'" )


# ── State machine (SPEC §5). All functions mutate gs and return a result. ───

def open_room(gs: dict, bus: list[dict], round_number: int, agent_id: str) -> dict:
    if agent_id not in AGENT_PROFILES:
        return {"error": "unknown_agent"}
    st = _agent_state(gs, agent_id)
    if st is None:
        return {"error": "agents_not_active"}
    stage = st.get("escalation_stage", "dormant")
    if stage not in ("hostile", "triggered"):
        return {"error": "not_hostile", "stage": stage,
                "detail": f"{AGENT_PROFILES[agent_id]['name']} will only take the meeting once things are hostile — today they are {stage}."}
    log = get_negotiation_log(gs)
    if log.get("active"):
        return {"error": "room_already_open", "agent_id": log["active"].get("agent_id")}
    if _meetings_this_round(gs, round_number) >= MAX_MEETINGS_PER_ROUND:
        return {"error": "meeting_cap_reached", "cap": MAX_MEETINGS_PER_ROUND}
    # Entry fee — win or lose, walking in has a price.
    gs["corporate_treasury"] = round((gs.get("corporate_treasury") or 0) - MEETING_FEE, 2)
    grievances = compute_grievances(gs, bus, agent_id)
    profile = AGENT_PROFILES[agent_id]
    room = {
        "agent_id": agent_id, "round": round_number, "opened_at": _now(),
        "fee_paid": MEETING_FEE, "turns": [], "deals": [], "status": "open",
        "persona": {"name": profile["name"], "title": profile["title"],
                    "icon": profile["icon"], "avatar": profile.get("avatar_emoji", profile["icon"]),
                    "stage": stage, "personality": profile.get("personality")},
        "grievances": grievances,
    }
    opening = scripted_line(agent_id, stage, grievances, 0)
    room["turns"].append({"who": "agent", "text": opening, "at": _now()})
    log["active"] = room
    return {"room": room, "menu": menu_for_agent(gs, round_number, agent_id)}


def say(gs: dict, bus: list[dict], round_number: int, text: str) -> dict:
    log = get_negotiation_log(gs)
    room = log.get("active")
    if not room:
        return {"error": "no_open_room"}
    player_turns = sum(1 for t in room["turns"] if t["who"] == "player")
    if player_turns >= MAX_TURNS:
        return _close(gs, round_number, "turn_limit")
    text = (text or "").strip()[:500]
    if not text:
        return {"error": "empty_message"}
    room["turns"].append({"who": "player", "text": text, "at": _now()})
    # Phase 1: deterministic scripted reply. Phase 3 swaps this line for the
    # LLM contract; the room, menu and validation are identical either way.
    grievances = compute_grievances(gs, bus, room["agent_id"])
    reply = scripted_line(room["agent_id"], room["persona"]["stage"], grievances, player_turns + 1)
    room["turns"].append({"who": "agent", "text": reply, "at": _now()})
    return {"room": room, "menu": menu_for_agent(gs, round_number, room["agent_id"])}


def accept_concession(gs: dict, bus: list[dict], round_number: int, concession_id: str) -> dict:
    """Validate + apply one whitelisted concession. THE only path to state."""
    log = get_negotiation_log(gs)
    room = log.get("active")
    if not room:
        return {"error": "no_open_room"}
    agent_id = room["agent_id"]
    spec = CONCESSION_CATALOG.get(concession_id)
    if spec is None:
        return {"error": "unknown_concession", "concession_id": concession_id}
    if agent_id not in spec["agents"]:
        return {"error": "not_on_this_agents_menu", "agent_id": agent_id}
    # Per-meeting bound: one promised concession + one free action (SPEC §4).
    promised_already = any(d.get("promise_id") for d in room["deals"])
    if spec["promise"] and promised_already:
        return {"error": "one_promised_concession_per_meeting"}
    if not spec["promise"] and any(not d.get("promise_id") for d in room["deals"]):
        return {"error": "one_free_action_per_meeting"}

    price = priced_cost(gs, round_number, agent_id, concession_id)
    st = _agent_state(gs, agent_id)
    profile = AGENT_PROFILES[agent_id]

    # ── Apply: bounded, deterministic ──
    gs["corporate_treasury"] = round((gs.get("corporate_treasury") or 0) - price["cost"], 2)
    # Tolerance capped at the WATCHING threshold — deals buy you out of the
    # fire, not into being loved (SPEC rule 3).
    cap = profile["escalation_thresholds"]["watching"]
    old_tol = float(st.get("tolerance", 30) or 0)
    st["tolerance"] = round(max(old_tol, min(cap, old_tol + spec["tolerance"])), 1)

    eff = spec["effects"]
    if eff.get("reputation_delta"):
        gs["group_reputation"] = max(0, min(100, round((gs.get("group_reputation") or 50) + eff["reputation_delta"], 2)))
    if eff.get("governance_risk_delta"):
        for b in bus:
            b["governance_risk_score"] = max(0.0, min(100.0, round(
                float(b.get("governance_risk_score", 20) or 0) + eff["governance_risk_delta"], 2)))
    if eff.get("burnout_delta"):
        for b in bus:
            b["staff_burnout_index"] = max(0.0, min(100.0, round(
                float(b.get("staff_burnout_index", 0) or 0) + eff["burnout_delta"], 2)))
    if eff.get("flag"):
        fname, frounds = eff["flag"]
        gs.setdefault("active_event_flags", {})[fname] = {"active": True, "until_round": round_number + frounds}

    promise_rec = None
    if spec["promise"]:
        metrics = _compute_agent_metrics(gs, bus)
        base = float(metrics.get(spec["promise"]["metric"], 50) or 50)
        promise_rec = {
            "id": f"nego:{agent_id}:{concession_id}:R{round_number}",
            "agent_id": agent_id,
            "metric": spec["promise"]["metric"],
            "target": round(base + spec["promise"]["target_bump"], 1),
            "due_round": round_number + PROMISE_HORIZON,
            "state": "open",
            "source": "negotiation",
        }
        gs.setdefault("autonomous_agents", {}).setdefault("promises", []).append(promise_rec)

    deal = {
        "concession_id": concession_id, "label": spec["label"],
        "cost_paid": price["cost"], "multiplier": price["multiplier"],
        "tolerance_before": old_tol, "tolerance_after": st["tolerance"],
        "tolerance_cap": cap,
        "promise_id": (promise_rec or {}).get("id"),
        "at": _now(),
    }
    room["deals"].append(deal)
    name = profile["name"]
    ack = (f"{name}: 'The {spec['label']} is noted — and it will be verified."
           + (f" I expect {promise_rec['metric'].replace('_', ' ')} at {promise_rec['target']} by round {promise_rec['due_round']}. "
              f"Break that and we will not be meeting again on these terms.'" if promise_rec else "'"))
    room["turns"].append({"who": "agent", "text": ack, "at": _now()})
    return {"deal": deal, "promise": promise_rec, "room": room,
            "menu": menu_for_agent(gs, round_number, agent_id)}


def _close(gs: dict, round_number: int, resolution: str) -> dict:
    log = get_negotiation_log(gs)
    room = log.get("active")
    if not room:
        return {"error": "no_open_room"}
    room["status"] = "closed"
    room["resolution"] = resolution
    room["closed_at"] = _now()
    if resolution == "walk_out" and not room["deals"]:
        # stand_firm: the agent remembers being stonewalled (SPEC §4).
        st = _agent_state(gs, room["agent_id"])
        if st is not None:
            st["patience_counter"] = int(st.get("patience_counter", 0) or 0) + 1
    log["history"].append(room)
    log["active"] = None
    return {"closed": copy.deepcopy(room)}


def walk_out(gs: dict, round_number: int) -> dict:
    return _close(gs, round_number, "walk_out")


def close_on_commit(gs: dict, round_number: int) -> Optional[dict]:
    """Auto-close an open room when the round commits (fluency rule: a room
    never blocks or outlives the round). Returns the closed room or None."""
    log = gs.get("negotiation_log") or (gs.get("active_event_flags") or {}).get("negotiation_log")
    if not isinstance(log, dict) or not log.get("active"):
        return None
    res = _close(gs, round_number, "round_committed")
    return res.get("closed")
