"""
paradigm_registry.py — single dispatch point for per-paradigm round config (audit #15).

Round-config lookup was branched with `if paradigm == "un_sdg": ... elif ...`
chains duplicated across router.py (solo seeding, commit) and admin paths. Adding
a new paradigm meant finding and editing every chain, and it was easy to miss one
(the code already carries defensive fallbacks like `get_pillar_config(rnum) or
get_round_config(rnum)`).

This registry maps a paradigm -> a provider callable, so a new paradigm is added
in ONE place and every call site picks it up. Providers import their config
module lazily to preserve the existing import graph and avoid cycles.
"""

from __future__ import annotations

from typing import Callable, Optional

from round_configs import get_round_config


def _legacy(rnum: int):
    return get_round_config(rnum)


def _sdg(rnum: int):
    from sdg_configs import get_sdg_round_config
    return get_sdg_round_config(rnum)


def _healthcare(rnum: int):
    from healthcare_configs import get_healthcare_round_config
    return get_healthcare_round_config(rnum)


def _pillar(rnum: int):
    from pillar_configs import get_pillar_config
    # Pillar mode falls back to the legacy config when a pillar override is absent
    # for a round — preserving the previous `... or get_round_config(rnum)` behaviour.
    return get_pillar_config(rnum) or get_round_config(rnum)


# Paradigm -> provider. `advanced_climate` shares the legacy config (only its
# engine behaviour differs), matching the previous `else` branch.
_PROVIDERS: dict[str, Callable[[int], Optional[dict]]] = {
    "legacy_abc": _legacy,
    "advanced_climate": _legacy,
    "un_sdg": _sdg,
    "healthcare": _healthcare,
    "multi_toggles": _pillar,
}

VALID_PARADIGMS = frozenset(_PROVIDERS)


def round_config_for(paradigm: str, rnum: int):
    """Return the round config for (paradigm, round). Unknown/blank paradigms
    fall back to the legacy provider — the same default the old `else` gave."""
    return _PROVIDERS.get(paradigm or "legacy_abc", _legacy)(rnum)
