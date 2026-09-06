"""FIN-06 (audit 2026-09-04, Wave 3) — bridge the tick's consequence waterfall
to the treasury that is actually persisted.

WHAT WAS WRONG
    engine.process_tick's waterfall explained the treasury movement inside the
    tick, and its `final_treasury` / `entry_count` were struck in the
    reporting layer, before the regulatory-ratchet fine and the post-CSF flow
    surcharges (up to $9.9M apart from the tick's own output). Then the round
    kept moving the treasury OUTSIDE the tick — pillar costs, the option's
    treasury effect and the R5 cyclone damage in post_tick, NPC fines, agent
    events, cascades, biodiversity projects, the treasury floor and the
    balance sheet's short-term interest in run_new_engines — by up to $20M a
    round, with no entry anywhere. The facilitator teleprompter told the room
    the waterfall "shows EXACTLY how treasury moved from start to finish of the
    round"; the seam probe listed `consequence_waterfall.final_treasury` apart
    from every other surface for two waves.

WHAT THIS DOES
    process_tick now re-finalises its waterfall as its last act (engine.
    TickContext.finalise_waterfall) and run_new_engines records which engine
    moved the treasury by how much (`_treasury_moves`). The router measures the
    treasury after each stage — tick, pillar aggregates, post_tick, engines,
    persistence — and this module appends one entry per movement, in order,
    with the engine's own name on it; a stage's unattributed remainder becomes
    a labelled "other" entry rather than a silent gap. `final_treasury` then IS
    the persisted treasury, `initial + Σ entries == final` to the cent, and
    `bridge` records the stage figures for the diagnostics rail.
"""
from __future__ import annotations

from typing import Any

# The one label a frontend can rely on for the tick's own closing figure
ENGINE_FINAL_KEY = "engine_final_treasury"


def _severity(amount: float, base: float) -> dict:
    try:
        from engine import classify_severity
        return classify_severity(abs(amount), max(abs(base), 1.0))
    except Exception:  # pragma: no cover — never let a label break a commit
        return {"tier": "routine", "label": "Routine"}


def _post_tick_items(events: dict, delta: float) -> list[tuple[str, float, str]]:
    """Itemise post_tick's movement from the ledgers it already writes."""
    items: list[tuple[str, float, str]] = []
    remaining = delta
    opt = events.get("ledger_option_treasury")
    if isinstance(opt, (int, float)) and abs(opt) >= 0.01:
        items.append(("Round option — treasury effect", round(float(opt), 2),
                      "The chosen option's own treasury impact (cost or windfall), applied after the tick."))
        remaining = round(remaining - float(opt), 2)
    dmg = events.get("actual_damage")
    if events.get("climate_event_struck") and isinstance(dmg, (int, float)) and abs(dmg) >= 0.01:
        items.append(("Climate event damage", round(-float(dmg), 2),
                      "Physical damage from the round's climate event, net of resilience."))
        remaining = round(remaining + float(dmg), 2)
    if abs(remaining) >= 0.01:
        items.append(("Other round effects (post-tick)", remaining,
                      "Round-specific mechanics applied after the tick that carry no ledger of their own."))
    return items


def bridge_waterfall(
    events: dict,
    *,
    after_tick: float,
    after_pillar: float,
    after_post_tick: float,
    after_engines: float,
    stored: float,
) -> dict | None:
    """Extend events["consequence_waterfall"] so it closes on `stored`.

    Idempotent per commit (the bridge is stamped once; a second call on the
    same dict is a no-op). Returns the waterfall, or None when there is none.
    """
    wf = events.get("consequence_waterfall")
    if not isinstance(wf, dict) or "bridge" in wf:
        return wf if isinstance(wf, dict) else None
    entries = wf.get("entries")
    if not isinstance(entries, list):
        entries = []
        wf["entries"] = entries
    initial = float(wf.get("initial_treasury", after_tick) or 0.0)
    running = float(entries[-1]["running_total"]) if entries and "running_total" in entries[-1] else float(wf.get("final_treasury", after_tick) or 0.0)

    def add(label: str, amount: float, because: str, stage: str) -> None:
        nonlocal running
        if abs(amount) < 0.01:
            return
        running = round(running + amount, 2)
        entries.append({
            "label": label, "amount": round(amount, 2), "running_total": running,
            "severity": _severity(amount, initial), "because": because, "stage": stage,
        })

    # 1. pillar aggregates (multi_toggles / brsr_ngrbc) — applied by the router
    d_pillar = round(after_pillar - after_tick, 2)
    if abs(d_pillar) >= 0.01:
        add("Strategic pillar selections", d_pillar,
            "The cost of the pillar options chosen this round, owed whatever their effectiveness.", "pillar")

    # 2. post_tick — the round's scripted mechanics
    d_post = round(after_post_tick - after_pillar, 2)
    for label, amount, because in _post_tick_items(events, d_post):
        add(label, amount, because, "post_tick")

    # 3. run_new_engines — one entry per engine that moved the treasury
    d_eng = round(after_engines - after_post_tick, 2)
    attributed = 0.0
    for move in events.get("_treasury_moves") or []:
        try:
            amt = round(float(move.get("delta", 0.0)), 2)
        except (TypeError, ValueError):
            continue
        add(str(move.get("engine", "engine")), amt,
            "Treasury movement recorded by this engine after the tick.", "engines")
        attributed = round(attributed + amt, 2)
    rest = round(d_eng - attributed, 2)
    if abs(rest) >= 0.01:
        add("Other engine movements", rest,
            "Movement inside run_new_engines that no engine mark attributed.", "engines")

    # 4. anything between the engines and persistence
    d_late = round(stored - after_engines, 2)
    if abs(d_late) >= 0.01:
        add("Late adjustments before persistence", d_late,
            "Movement after the engines and before the round was saved.", "late")

    # closing figures: the PERSISTED treasury
    wf[ENGINE_FINAL_KEY] = round(after_tick, 2)
    wf["final_treasury"] = round(stored, 2)
    wf["net_change"] = round(stored - initial, 2)
    wf["entry_count"] = len(entries)
    wf["bridge"] = {
        "after_tick": round(after_tick, 2), "after_pillar": round(after_pillar, 2),
        "after_post_tick": round(after_post_tick, 2), "after_engines": round(after_engines, 2),
        "stored": round(stored, 2),
        "closes": abs(round(initial + sum(e["amount"] for e in entries) - stored, 2)) < 0.01 + 0.005 * len(entries),
    }
    return wf
