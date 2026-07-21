"""
Muressons — Deterministic per-cohort RNG (GAME-4)

Every stochastic event in the engine must roll identically for all teams in a
cohort, so that leaderboard rankings reflect strategy rather than luck. We
achieve this with *named, independent* random streams derived from a single
per-cohort seed:

    rng = event_rng(active_event_flags, round_number, "blackswan:ransomware")

Each (seed, round_number, event_name) triple yields its own Random instance.
Because every event has its own stream, decision-dependent branching in one
event can never desync the rolls of another — and adding a brand-new engine
later does not shift the rolls of existing ones.

If no seed is present (e.g. an ad-hoc demo/solo session, or a legacy session),
the helpers fall back to a system-seeded Random, preserving the previous
non-deterministic behaviour.
"""

from __future__ import annotations

import hashlib
import random
from typing import Optional


def _resolve_seed(flags: Optional[dict]) -> Optional[str]:
    """Pull the cohort stochastic seed out of an active_event_flags dict."""
    if not isinstance(flags, dict):
        return None
    seed = flags.get("stochastic_seed")
    return str(seed) if seed not in (None, "") else None


def event_seed(flags: Optional[dict], round_number: int, event_name: str) -> Optional[int]:
    """Stable integer seed for a named event, or None when unseeded.

    Uses SHA-256 (not Python's hash(), which is per-process randomised) so the
    same inputs always map to the same seed across processes and restarts.
    """
    base = _resolve_seed(flags)
    if base is None:
        return None
    digest = hashlib.sha256(f"{base}|{round_number}|{event_name}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def event_rng(flags: Optional[dict], round_number: int, event_name: str) -> random.Random:
    """Independent Random stream for a named event.

    Seeded deterministically from the cohort seed when present; system-seeded
    (non-deterministic) otherwise.
    """
    seed = event_seed(flags, round_number, event_name)
    return random.Random(seed) if seed is not None else random.Random()
