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


def derive_cohort_seed(cohort_id: str) -> str:
    """The seed a cohort gets when nobody chose one (4.2, 2026-08-03).

    WHY AUTO-GENERATE AT ALL
        `rng_seed` has always been a cohort setting, defaulting to "". Empty
        means unseeded, and unseeded means event_rng() hands back a
        system-seeded Random — so the black swans, micro-strikes and NPC
        reactions a team met were unrepeatable and unrecorded. Reproducibility
        was available, spelled correctly, and off by default: an unticked
        checkbox in the one place a graded run cannot afford one. A facilitator
        who never opened the advanced settings ran an ungradeable simulation
        and got no warning.

    WHY DERIVED FROM THE COHORT ID RATHER THAN RANDOM
        The seed is then a pure function of something already persisted, so it
        can be recomputed if the flag is ever lost, and reading it tells you
        which run it belongs to. It is not secret and does not need to be
        unpredictable — it needs to be STABLE and RECORDED.

    WHY THE COHORT ID AND NOT THE SESSION ID
        Every team in a cohort must roll identically or the leaderboard ranks
        luck rather than strategy (GAME-4). Children derive from their parent's
        id, so a twenty-team cohort shares one stream without any lookup.
    """
    digest = hashlib.sha256(f"muressons-cohort|{cohort_id}".encode("utf-8")).hexdigest()
    return f"mur-{digest[:12]}"


def resolve_or_derive_seed(flags: Optional[dict], cohort_id: str) -> str:
    """The seed this cohort WILL use, without touching anything.

    Pure on purpose. create_session needs the seed value before the live flags
    dict exists (to stamp provenance, 4.7) and again afterwards (to stamp the
    flags themselves, 4.2). Both call this, so the value recorded as provenance
    and the value the engine actually rolls with cannot disagree — the failure
    mode that would make provenance worse than useless, because it would be
    confidently wrong rather than absent.
    """
    return _resolve_seed(flags) or derive_cohort_seed(cohort_id)


def ensure_cohort_seed(flags: dict, cohort_id: str) -> str:
    """Stamp the resolved seed onto `flags` unless one is already set.

    Never overwrites: an explicit seed from the facilitator, or an inherited
    one, always wins. Returns the seed now in effect.
    """
    seed = resolve_or_derive_seed(flags, cohort_id)
    flags["stochastic_seed"] = seed
    return seed
