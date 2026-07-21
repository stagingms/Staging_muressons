"""Cohort player capacity — one resolver, one ceiling.

Before this module the limit was the literal `10` written at two enforcement
sites (`induct_player` and `generate_player_id`). Two literals is one literal
too many: raising the cap meant finding both, and a miss would have let one
path admit players the other rejected.

Policy (July 2026, set by the product owner):
  * A cohort may be configured for FEWER players, but never more than 20.
    `max_players` is therefore clamped on the way IN (settings normalisation)
    and again on the way OUT (`resolve_max_players`) — a value persisted by an
    older build, or hand-edited into a snapshot, cannot exceed the ceiling.
  * The default is the ceiling. A facilitator who never touches the setting
    gets 20, which is what "allow up to 20 players" means in practice.

The two enforcement sites count DIFFERENT things — `induct_player` counts the
in-process registry, `generate_player_id` counts the session's
`registered_players` — so this module deliberately exposes the limit and the
error text rather than a "check" helper that would have to guess the source of
truth for the current headcount.
"""

MAX_PLAYERS_CEILING = 20
"""Absolute upper bound. Not configurable — a cohort larger than this has never
been exercised by the round engine's peer-comparison or leaderboard paths."""

DEFAULT_MAX_PLAYERS = MAX_PLAYERS_CEILING


def clamp_max_players(value, default: int = DEFAULT_MAX_PLAYERS) -> int:
    """Coerce an arbitrary configured value into 1..MAX_PLAYERS_CEILING.

    Non-numeric or absent → `default`. A cohort of zero players is not a
    meaningful configuration (it would make the cohort unjoinable while
    reporting success), so the floor is 1.
    """
    if value is None or isinstance(value, bool):
        return default
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(MAX_PLAYERS_CEILING, n))


def resolve_max_players(settings: dict | None) -> int:
    """The effective cap for a cohort, given its effective settings dict."""
    if not settings:
        return DEFAULT_MAX_PLAYERS
    return clamp_max_players(settings.get("max_players"))


def capacity_error(limit: int) -> str:
    """The 400 detail shown when a cohort is full.

    Names the configured limit rather than a hardcoded number: a facilitator who
    set their cohort to 12 should be told 12, not 20, or they will assume the
    system is broken.
    """
    return f"Cohort has reached its maximum of {limit} players."
