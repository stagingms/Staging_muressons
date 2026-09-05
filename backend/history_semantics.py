"""history_semantics — one reading of the round history.

Audit 2026-09-04 SEAM-08 / WP-19.

Convention: history row K is the state ENTERING round K (row 1 is the seed,
row 2 the state after committing round 1, …). Every consumer that computes
a per-round delta relies on it. The R10 commit breaks it: it persists the
CLOSING state in place of row 10 (there is no round 11 to insert), so the
state entering round 10 was lost from every history consumer — analytics
attributed R9 + R10 to "R9", the debrief's R9 deltas were wrong and R10 had
no entry at all.

The R10 commit now stashes the entering-R10 state (the row it is about to
overwrite) under flags[ENTERING_R10_BAG]; both stores hand their raw rows
through `splice_final_state`, which restores row 10 from the stash and,
when the caller asks (`include_final=True`), appends the closing state as
round 11 flagged `is_final`. `fetch_latest_state` is untouched: the latest
state is still the closing state, round_number 10, game_over set.

Consumer helpers: a consumer that wants "the team's current state" fetches
with include_final=True and reads `history[-1]` (the closing row once the
run is complete, else the entering row of the current round); it reports
the round through `display_round` (10 for the closing row, never 11).
A consumer that lists events produced BY a round reads them off the row
that round's commit wrote — `produced_by_round` (row K holds the events
of the round-(K-1) commit; the seed row holds none).
"""
from __future__ import annotations

import copy
from typing import Any

ENTERING_R10_BAG = "_entering_r10_state"
FINAL_ROUND_NUMBER = 11


def stash_entering_state(new_global: dict, entering_global: dict, entering_bus: list[dict]) -> None:
    """Called by the R10 commit before the in-place persist: remember the
    state the round started from, so history can still show it."""
    flags = new_global.setdefault("active_event_flags", {})
    gs = copy.deepcopy(entering_global or {})
    # the stash must not nest an earlier stash or the DNA snapshot
    inner = gs.get("active_event_flags")
    if isinstance(inner, dict):
        inner.pop(ENTERING_R10_BAG, None)
        inner.pop("consequence_dna_snapshot", None)
    flags[ENTERING_R10_BAG] = {
        "round_number": 10,
        "global_state": gs,
        "business_units": copy.deepcopy(entering_bus or []),
    }


def splice_final_state(history: list[dict], include_final: bool = False) -> list[dict]:
    """Restore the entering-R10 row from the stash; optionally append the
    closing state as a final row (round 11, is_final). A history whose last
    row is not a completed round 10 is returned unchanged."""
    if not history:
        return history
    last = history[-1]
    try:
        if int(last.get("round_number", 0)) != 10:
            return history
    except (TypeError, ValueError):
        return history
    last_gs = last.get("global_state") or {}
    flags = last_gs.get("active_event_flags") or {}
    bag = flags.get(ENTERING_R10_BAG)
    if not isinstance(bag, dict) or not isinstance(bag.get("global_state"), dict):
        return history
    entering_gs = dict(bag["global_state"])
    # the same top-level unpacking of non-column flag keys the stores apply
    for k, v in (entering_gs.get("active_event_flags") or {}).items():
        if k not in entering_gs:
            entering_gs[k] = v
    entering_row: dict[str, Any] = {
        **{k: v for k, v in last.items() if k not in ("global_state", "business_units")},
        "round_number": 10,
        "global_state": entering_gs,
        "business_units": bag.get("business_units") or last.get("business_units") or [],
    }
    out = list(history[:-1]) + [entering_row]
    if include_final:
        final_gs = dict(last_gs)
        final_flags = dict(flags)
        final_flags.pop(ENTERING_R10_BAG, None)
        final_gs["active_event_flags"] = final_flags
        final_gs.pop(ENTERING_R10_BAG, None)
        out.append({**last, "round_number": FINAL_ROUND_NUMBER, "is_final": True,
                    "global_state": final_gs, "decisions": []})
    return out


def display_round(row: dict) -> int:
    """The round a row belongs to as a player or facilitator would say it:
    the closing row is "round 10 (finished)", not "round 11"."""
    try:
        rn = int(row.get("round_number", 1) or 1)
    except (TypeError, ValueError):
        rn = 1
    return 10 if row.get("is_final") else rn


def produced_by_round(row: dict) -> int | None:
    """The round whose commit wrote this row (row K = state entering K, so
    its events came from the round-(K-1) commit). None for the seed row."""
    if row.get("is_final"):
        return 10
    try:
        rn = int(row.get("round_number", 1) or 1)
    except (TypeError, ValueError):
        return None
    return rn - 1 if rn >= 2 else None


def entering_rows(history: list[dict]) -> list[dict]:
    """Rows 1..10 only — drops the closing row a caller fetched with
    include_final=True but does not want in a per-round series."""
    return [h for h in (history or []) if not h.get("is_final")]
