"""
Muressons — Stakeholder Engagement Actions & Promise Ledger (SPEC F5)
═══════════════════════════════════════════════════════════════════════════
The "dialogic verb": lets a player act on a *specific* stakeholder each round —
a town hall (goodwill now, no promise), a public pledge or a private commitment
(goodwill now PLUS a promise with a metric target and a due round). Promises are
then judged: kept ones pay a trust / SLO / reputation dividend; broken ones fire
the F1 betrayal scar and a reputation ding — which is what makes a pledge a real
decision rather than free points.

Design / persistence notes:
  • Entirely gated on the `stakeholder_engagement_enabled` toggle (default off);
    with it off, nothing here runs and behaviour is unchanged.
  • The promise ledger lives in `npc_stakeholders["promises"]` (not a new
    global_state key) so it persists via the §1.7 carry-forward WITHOUT expanding
    the `_assemble_global_state` whitelist or touching `GlobalStateOut`.
  • Trust bumps and scars respect the same scar-ceiling semantics as F1, so a
    betrayed stakeholder cannot be instantly bought back with a town hall.
  • Deterministic — no RNG.
"""

from __future__ import annotations
from typing import Any


# type → whether making it registers a forward promise
ENGAGEMENT_CATALOG: dict[str, dict] = {
    "town_hall":          {"creates_promise": False},
    "public_pledge":      {"creates_promise": True},
    "private_commitment": {"creates_promise": True},
}

# metrics a promise can be written against (evaluated at the due round)
_SUPPORTED_METRICS = ("social_license_score", "group_reputation", "trust")


def _engagement_consts() -> dict:
    """Pull engagement tunables from config (config-Excel backed)."""
    from config import (
        ENGAGE_TOWNHALL_COST, ENGAGE_TOWNHALL_TRUST,
        ENGAGE_PLEDGE_COST, ENGAGE_PLEDGE_TRUST,
        ENGAGE_COMMIT_COST, ENGAGE_COMMIT_TRUST,
        PROMISE_DEFAULT_HORIZON, PROMISE_KEPT_TRUST_BONUS,
        PROMISE_KEPT_SLO_CREDIT, PROMISE_KEPT_REP_CREDIT, PROMISE_BROKEN_REP_DING,
        TRUST_SCAR_IMMEDIATE, TRUST_SCAR_DURATION, TRUST_SCAR_CEILING,
    )
    return {
        "cost":  {"town_hall": ENGAGE_TOWNHALL_COST, "public_pledge": ENGAGE_PLEDGE_COST, "private_commitment": ENGAGE_COMMIT_COST},
        "trust": {"town_hall": ENGAGE_TOWNHALL_TRUST, "public_pledge": ENGAGE_PLEDGE_TRUST, "private_commitment": ENGAGE_COMMIT_TRUST},
        "default_horizon":  PROMISE_DEFAULT_HORIZON,
        "kept_trust_bonus": PROMISE_KEPT_TRUST_BONUS,
        "kept_slo_credit":  PROMISE_KEPT_SLO_CREDIT,
        "kept_rep_credit":  PROMISE_KEPT_REP_CREDIT,
        "broken_rep_ding":  PROMISE_BROKEN_REP_DING,
        "scar_immediate":   TRUST_SCAR_IMMEDIATE,
        "scar_duration":    TRUST_SCAR_DURATION,
        "scar_ceiling":     TRUST_SCAR_CEILING,
    }


def _bump_trust(npc_state: dict, amount: float, round_number: int, scar_ceiling: float) -> float:
    """Apply a trust delta respecting the active scar ceiling and [0,100] bounds."""
    prev = float(npc_state.get("trust", 50.0))
    scar_until = int(npc_state.get("scar_until", 0))
    ceiling = scar_ceiling if round_number <= scar_until else 100.0
    npc_state["trust"] = round(max(0.0, min(ceiling, prev + amount)), 2)
    # a bump means the stock is now meaningfully set (avoid the F1 re-seed path)
    npc_state["trust_initialised"] = True
    return npc_state["trust"]


def _measure(metric: str, npc_id: str, npc_state: dict, global_state: dict, bus_states: list[dict]) -> float | None:
    """Current value of a promise's target metric, or None if unmeasurable."""
    if metric == "group_reputation":
        return float(global_state.get("group_reputation", 50))
    if metric == "trust":
        return float(npc_state.get("trust", 50))
    if metric == "social_license_score":
        from npc_stakeholders import _attached_bus
        targets = _attached_bus(npc_id, bus_states) or bus_states
        if not targets:
            return None
        return sum(b.get("social_license_score", 50) for b in targets) / len(targets)
    return None


def apply_engagement_action(
    npc_master_state: dict,
    global_state: dict,
    action: dict,
    round_number: int,
    consts: dict | None = None,
) -> dict:
    """
    Apply this round's engagement action. Deducts the treasury cost, bumps the
    target NPC's trust now, and (for pledge/commitment) registers a promise in the
    ledger. Returns a result dict; invalid actions are reported, not raised.
    """
    consts = consts or _engagement_consts()
    a_type = (action or {}).get("type")
    npc_id = (action or {}).get("npc_id")
    spec = ENGAGEMENT_CATALOG.get(a_type)
    npcs = npc_master_state.get("npcs", {})

    if spec is None or npc_id not in npcs:
        return {"error": "invalid_engagement", "type": a_type, "npc_id": npc_id}

    st = npcs[npc_id]
    cost = consts["cost"][a_type]
    global_state["corporate_treasury"] = round(global_state.get("corporate_treasury", 0) - cost, 2)
    new_trust = _bump_trust(st, consts["trust"][a_type], round_number, consts["scar_ceiling"])

    result = {"type": a_type, "npc_id": npc_id, "cost": cost, "trust_now": new_trust}

    if spec["creates_promise"]:
        metric = action.get("metric", "social_license_score")
        if metric not in _SUPPORTED_METRICS:
            metric = "social_license_score"
        horizon = int(action.get("horizon", consts["default_horizon"]))
        promise = {
            "id": f"{npc_id}:{a_type}:R{round_number}",
            "npc_id": npc_id,
            "type": a_type,
            "metric": metric,
            "target": float(action.get("target", 60)),
            "made_round": round_number,
            "due_round": round_number + max(1, horizon),
            "cost": cost,
            "state": "open",
        }
        npc_master_state.setdefault("promises", []).append(promise)
        result["promise"] = promise

    return result


def resolve_promises(
    npc_master_state: dict,
    global_state: dict,
    bus_states: list[dict],
    round_number: int,
    consts: dict | None = None,
) -> list[dict]:
    """
    Judge every open promise whose due round has arrived. Kept → trust bonus +
    SLO credit (to the NPC's attached BUs) + reputation credit. Broken → the F1
    betrayal scar (hard trust hit + recovery ceiling for SCAR_DURATION rounds) +
    a reputation ding. Each promise resolves exactly once (state flips off "open").
    Returns the list of resolutions for UI/debrief.
    """
    consts = consts or _engagement_consts()
    ledger = npc_master_state.setdefault("promises", [])
    npcs = npc_master_state.get("npcs", {})
    resolutions: list[dict] = []

    for p in ledger:
        if p.get("state") != "open" or int(p.get("due_round", 0)) > round_number:
            continue
        npc_id = p["npc_id"]
        st = npcs.get(npc_id)
        if st is None:
            p["state"] = "void"
            continue

        val = _measure(p["metric"], npc_id, st, global_state, bus_states)
        kept = val is not None and val >= float(p["target"])

        if kept:
            _bump_trust(st, consts["kept_trust_bonus"], round_number, consts["scar_ceiling"])
            from npc_stakeholders import _attached_bus
            for bu in (_attached_bus(npc_id, bus_states) or bus_states):
                bu["social_license_score"] = max(0.0, min(100.0, round(
                    bu.get("social_license_score", 50) + consts["kept_slo_credit"], 2
                )))
            global_state["group_reputation"] = max(0, min(100, round(
                global_state.get("group_reputation", 50) + consts["kept_rep_credit"], 2
            )))
            p["state"] = "kept"
        else:
            # Broken promise → F1 betrayal scar (mirrors update_trust's scar path).
            prev = float(st.get("trust", 50.0))
            st["trust"] = round(max(0.0, prev - consts["scar_immediate"]), 2)
            st["scar_until"] = round_number + consts["scar_duration"]
            st["trust_initialised"] = True
            global_state["group_reputation"] = max(0, round(
                global_state.get("group_reputation", 50) - consts["broken_rep_ding"], 2
            ))
            p["state"] = "broken"

        p["resolved_round"] = round_number
        p["measured"] = round(val, 2) if isinstance(val, (int, float)) else None
        resolutions.append({
            "id": p["id"], "npc_id": npc_id, "state": p["state"],
            "metric": p["metric"], "target": p["target"], "measured": p["measured"],
        })

    return resolutions
