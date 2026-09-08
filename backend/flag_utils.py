"""flag_utils — the one reading of the flag namespace.

Audit 2026-09-04 F-15 / WP-14. The R10 finale reads a team's flags through
collect_all_flags (booleans, string values, and the `rN_flags` / `*flag*`
lists the option layer writes), while the mid-game preview, the
Consequence-DNA projection and the What-If replay handed calculate_mr the
RAW dict — in which `synergy_unlock`, `ethical_ai_overhaul`, `community_fund`
… live only inside `r7_flags: [...]` lists, so every strategic flag was
invisible: estimates understated the award by up to 0.57 and the Mirror
Debrief told teams they had missed the lever they took.

This module has no simulation imports, so engine.py, round_logic.py and the
API layers can all import it without a cycle. round_logic._collect_all_flags
is an alias of collect_all_flags.
"""
from __future__ import annotations

from typing import Any


# ═══════════════════════════════════════════════════════════════════════
#  The finale's re-run record is STORAGE, not a flag
# ═══════════════════════════════════════════════════════════════════════
# round_logic._stamp_finale_valuation has to be re-runnable on the CLOSING
# state (audit F-08 / SEAM-05), so the R10 handler records the inputs it
# resolved and router.commit_turn replays them after the engines. That record
# carries `all_flags` — a snapshot of every flag in force at R10 — and it was
# parked under a bare key in active_event_flags, which IS the flag namespace.
#
# collect_all_flags below recurses into any nested dict whose key is not
# underscore-prefixed, and harvests every list under a key containing "flag".
# So the record handed the whole game's flag history back to any consumer that
# asked the R10 events bag what was set THIS round. Measured in Phase 5
# (docs/verification/phase5_recalibration.md): npc_stakeholders.detect_betrayal
# fired a third time at R10 on `deny_and_deflect`, a flag the team set once at
# R4 — one decision, two trust scars — and the same record also contributed
# `is_healthcare`, `brsr` and every boolean inside the pathway `special` config
# as flag names. In the closing bag it resurrected flags the round had already
# cleared (`insolvency_warning`, `phase_transition`, `micro_strike_triggered`).
#
# The convention for exactly this case is already stated below: an underscore
# prefix marks a private state bag as storage rather than a flag. The record
# now follows it. FINALE_INPUTS_LEGACY_KEY is read but never written, so a
# session persisted before this change still restamps.
FINALE_INPUTS_KEY = "_finale_inputs"
FINALE_INPUTS_LEGACY_KEY = "finale_inputs"


def finale_inputs_of(*bags: Any) -> dict:
    """The finale's re-run record, from the first bag that carries it under
    either key. Returns {} when the finale has not run — which is what
    router.commit_turn and restamp_finale_valuation test for."""
    for bag in bags:
        if not isinstance(bag, dict):
            continue
        for key in (FINALE_INPUTS_KEY, FINALE_INPUTS_LEGACY_KEY):
            record = bag.get(key)
            if isinstance(record, dict) and record:
                return record
    return {}


def collect_all_flags(flags_dict: dict) -> set[str]:
    """
    FIX AUDIT-008: Collect boolean keys and specific flag lists (e.g., rX_flags),
    rather than recursively slurping every string value in the event dictionary.
    """
    result = set()
    for key, val in flags_dict.items():
        if not isinstance(key, str):
            continue  # Skip non-string keys (e.g. SDG integer indices)
        if key.startswith("_"):
            # Private state bags (e.g. _materiality_idempotency, whose nested
            # debrief carries booleans like governance_board/q1_recall) are
            # storage, not flags — recursing into them polluted the flag
            # namespace with names no writer ever intended as flags.
            continue
        if "flag" in key.lower():
            if isinstance(val, list):
                result.update(str(v) for v in val)
            elif isinstance(val, str):
                result.add(val)
        elif isinstance(val, bool) and val:
            # Explicit boolean states are valid flags (e.g. cfo_override_used: True)
            result.add(key)
        elif isinstance(val, dict):
            # Recurse to find nested booleans or flag lists
            result.update(collect_all_flags(val))
            
    # Fallback to check specific critical string keys if they weren't matched
    for flag_key in [
        "electronics_blindspot", "deep_audit_completed",
        "electronics_blindspot_triggered", "deep_audit_protected",
    ]:
        if flag_key in flags_dict:
            result.add(flag_key)
    return result


def hr_investment_rounds_from(flags: dict) -> int:
    """Rounds in which HR quality was invested — the `hr_invested_r{N}` keys
    round_logic writes (the finale's own count, _post_r10_grand_finale)."""
    return sum(
        1 for k, v in (flags or {}).items()
        if isinstance(k, str) and k.startswith("hr_invested_r") and v is True
    )


def mr_flags_from(flags: dict) -> dict:
    """The flags dict calculate_mr should read, built exactly as the finale
    builds it: every collected flag name → True, plus the NUMERIC
    brsr_net_positive_dividend carried with its value (calculate_mr adds it)."""
    out = {f: True for f in collect_all_flags(flags or {})}
    out.pop("brsr_net_positive_dividend", None)
    div = (flags or {}).get("brsr_net_positive_dividend")
    if isinstance(div, (int, float)) and not isinstance(div, bool) and div:
        out["brsr_net_positive_dividend"] = div
    return out


def mr_input_from_state(global_state: dict, events: dict | None = None) -> tuple[dict, int]:
    """(flags for calculate_mr, hr_investment_rounds) for a state — optionally
    with this tick's not-yet-merged events layered on top, which is what the
    engine's preview sees mid-commit. Every non-finale caller of calculate_mr
    goes through here so the projection and the award read the same flags."""
    merged: dict[str, Any] = dict((global_state or {}).get("active_event_flags") or {})
    if events:
        merged.update({k: v for k, v in events.items() if isinstance(k, str) and not k.startswith("_")})
    return mr_flags_from(merged), hr_investment_rounds_from(merged)
