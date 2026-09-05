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
