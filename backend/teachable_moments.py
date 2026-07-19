"""
teachable_moments.py  (B5)
==========================
Read-only facilitator "teachable moment" detector.

When a meaningful fraction of a cohort's teams converge on a decision flag that
the flag-dependency graph marks as adverse (doubles a crisis, BLOCKS a bonus,
triggers a penalty), the facilitator gets a non-blocking prompt to pause and
discuss. Players see nothing — this is a facilitator-only read over data the
engine already produces.

Design notes:
  * `derive_teachable_moments()` is PURE — it takes a list of per-team flag
    collections and returns notes. No DB, no I/O → trivially unit-testable.
  * `compute_cohort_teachable_moments()` wraps it with the live cohort lookup,
    reusing the same session model the analytics endpoints use.
Nothing here mutates game state.
"""

from __future__ import annotations

from typing import Iterable

# Adverse-effect keywords: an entry in the flag-dependency graph whose `effect`
# contains any of these is treated as "convergence on this flag hurts the team".
_ADVERSE_KEYWORDS = ("blocks", "doubles", "triggers", "penalty", "forfeit", "loss")


def _is_adverse(effect: str) -> bool:
    e = (effect or "").lower()
    # "Prevents ... scandal" is protective, not adverse — exclude prevents.
    if "prevent" in e:
        return False
    return any(k in e for k in _ADVERSE_KEYWORDS)


def _load_adverse_flags() -> dict[str, dict]:
    """Map flag -> dependency entry, for flags whose effect is adverse."""
    try:
        from terminal_valuation import FLAG_DEPENDENCY_GRAPH
    except Exception:
        return {}
    out: dict[str, dict] = {}
    for dep in FLAG_DEPENDENCY_GRAPH:
        if _is_adverse(dep.get("effect", "")):
            out[dep["flag"]] = dep
    return out


def derive_teachable_moments(
    team_flag_sets: list[Iterable[str]],
    threshold_ratio: float = 0.5,
    min_teams: int = 2,
) -> list[dict]:
    """Return teachable-moment notes for a cohort.

    Parameters
    ----------
    team_flag_sets : one iterable of active flag names per team.
    threshold_ratio: fraction of teams that must share an adverse flag to fire.
    min_teams      : never fire for a cohort smaller than this.

    Returns a list of dicts: {flag, count, total, effect, category,
    source_round, target_round, message}, sorted by how many teams converged.
    """
    total = len(team_flag_sets)
    if total < min_teams:
        return []

    adverse = _load_adverse_flags()
    if not adverse:
        return []

    # Tally how many teams carry each adverse flag.
    counts: dict[str, int] = {}
    for flags in team_flag_sets:
        seen = set(flags or [])
        for flag in seen:
            if flag in adverse:
                counts[flag] = counts.get(flag, 0) + 1

    notes: list[dict] = []
    for flag, count in counts.items():
        if count / total < threshold_ratio:
            continue
        dep = adverse[flag]
        notes.append({
            "flag": flag,
            "count": count,
            "total": total,
            "effect": dep.get("effect", ""),
            "category": dep.get("category", "other"),
            "source_round": dep.get("source_round"),
            "target_round": dep.get("target_round"),
            "message": (
                f"{count}/{total} teams carry ‘{flag}’ "
                f"(from R{dep.get('source_round')}) → {dep.get('effect','')}. "
                f"Pause and discuss before R{dep.get('target_round')}."
            ),
        })

    notes.sort(key=lambda n: n["count"], reverse=True)
    return notes


async def compute_cohort_teachable_moments(cohort_id: str, threshold_ratio: float = 0.5) -> dict:
    """Live wrapper: gather each team's active flags in the cohort, then derive."""
    # Railway audit §1.1: this imported database_memory directly, so under
    # Postgres both the session scan AND fetch_latest_state ran against the
    # (empty) memory module. Route through the active store instead.
    import database as db

    # Player (team) sessions are the child sessions of this cohort.
    player_sessions = [
        s["session_id"] for s in await db.fetch_all_sessions_raw()
        if s.get("parent_cohort_id") == cohort_id
    ]

    team_flag_sets: list[list[str]] = []
    for sid in player_sessions:
        try:
            latest = await db.fetch_latest_state(sid)
        except Exception:
            latest = None
        if not latest:
            continue
        flags_dict = (latest.get("global_state") or {}).get("active_event_flags") or {}
        # active flags are truthy entries in the dict
        active = [k for k, v in flags_dict.items() if v]
        team_flag_sets.append(active)

    notes = derive_teachable_moments(team_flag_sets, threshold_ratio=threshold_ratio)
    return {
        "cohort_id": cohort_id,
        "teams_evaluated": len(team_flag_sets),
        "teachable_moments": notes,
    }
