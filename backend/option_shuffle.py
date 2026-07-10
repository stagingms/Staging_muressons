"""
Muressons Global Corporation — Option Presentation Shuffle Engine

ANTI-GAMING MEASURE: Randomizes the A/B/C label ordering per session
and per round so that the letter labels carry no signal about option
quality. A player can no longer infer that "Option A" is always the
boldest/best choice.

Architecture:
    - Each session gets a random shuffle_seed at creation time.
    - For each round, a deterministic permutation is derived from
      (shuffle_seed, round_number) so the same session always sees the
      same ordering (important for resuming / refreshing).
    - The API layer applies the shuffle when SERVING options to the
      frontend, and reverses it when RECEIVING choices back.
    - All backend logic (round_logic, engine, flags) continues to use
      canonical keys (option_a, option_b, option_c) unchanged.

Example:
    If round 6 shuffles to [option_c, option_a, option_b]:
    - Frontend sees: A="Monetise the Algorithm", B="Ethical AI Overhaul", C="Quiet Patch"
      becomes:       A="Quiet Patch", B="Monetise the Algorithm", C="Ethical AI Overhaul"
    - Player picks "option_a" (displayed as A) → backend receives "option_a"
      → deshuffle maps it back to canonical "option_c" (Quiet Patch)
"""

from __future__ import annotations
import random
from typing import Any


# The three canonical option keys in their default order
_CANONICAL_KEYS = ["option_a", "option_b", "option_c"]

# Display labels assigned to positions
_DISPLAY_LABELS = ["A", "B", "C"]


def generate_shuffle_seed() -> int:
    """Generate a random seed for a new session's option shuffle."""
    return random.randint(100_000, 999_999)


def _get_permutation(shuffle_seed: int, round_number: int) -> list[str]:
    """
    Return a deterministic permutation of canonical keys for a given
    session seed + round number combination.

    Returns e.g. ["option_c", "option_a", "option_b"] meaning:
      Display position A shows canonical option_c
      Display position B shows canonical option_a
      Display position C shows canonical option_b
    """
    rng = random.Random(shuffle_seed * 1000 + round_number)
    perm = list(_CANONICAL_KEYS)
    rng.shuffle(perm)
    return perm


def get_shuffle_mapping(shuffle_seed: int, round_number: int) -> dict:
    """
    Return the full shuffle mapping for a round.

    Returns:
        {
            "display_to_canonical": {"option_a": "option_c", "option_b": "option_a", ...},
            "canonical_to_display": {"option_c": "option_a", "option_a": "option_b", ...},
            "permutation": ["option_c", "option_a", "option_b"],
        }
    """
    perm = _get_permutation(shuffle_seed, round_number)

    # display_to_canonical: maps the displayed position key → the real canonical key
    # e.g. if perm = [option_c, option_a, option_b]:
    #   display "option_a" (position 0) → canonical "option_c" (perm[0])
    display_to_canonical = {}
    canonical_to_display = {}
    for i, display_key in enumerate(_CANONICAL_KEYS):
        canonical_key = perm[i]
        display_to_canonical[display_key] = canonical_key
        canonical_to_display[canonical_key] = display_key

    return {
        "display_to_canonical": display_to_canonical,
        "canonical_to_display": canonical_to_display,
        "permutation": perm,
    }


def shuffle_options_for_display(
    options: dict[str, Any],
    shuffle_seed: int,
    round_number: int,
) -> dict[str, Any]:
    """
    Reorder the options dict so that the canonical options are presented
    under shuffled display keys.

    Input:  {"option_a": {real A data}, "option_b": {real B data}, "option_c": {real C data}}
    Output: {"option_a": {real X data, label="A"}, "option_b": {real Y data, label="B"}, ...}

    The output dict always has keys option_a, option_b, option_c but the
    VALUES (title, description, impacts, flags) come from different
    canonical options depending on the shuffle.
    """
    if not options or shuffle_seed is None:
        return options

    mapping = get_shuffle_mapping(shuffle_seed, round_number)
    d2c = mapping["display_to_canonical"]

    shuffled = {}
    for display_key in _CANONICAL_KEYS:
        canonical_key = d2c[display_key]
        if canonical_key not in options:
            continue
        # Deep copy the canonical option data into the display slot
        opt_data = dict(options[canonical_key])
        # Override the label to match the display position
        display_label = display_key.replace("option_", "").upper()
        opt_data["label"] = display_label
        # Store the canonical key as metadata (NOT exposed to frontend —
        # stripped before sending response)
        opt_data["_canonical_key"] = canonical_key
        shuffled[display_key] = opt_data

    # Include any non-standard option keys (e.g., turnaround "option_t")
    for key in options:
        if key not in _CANONICAL_KEYS:
            shuffled[key] = dict(options[key])

    return shuffled


def deshuffle_choice(
    display_choice: str,
    shuffle_seed: int,
    round_number: int,
) -> str:
    """
    Map a player's displayed choice back to the canonical option key.

    Args:
        display_choice: The key the player selected (e.g. "option_a")
        shuffle_seed: The session's shuffle seed
        round_number: Current round number

    Returns:
        The canonical key (e.g. "option_c" if the shuffle mapped
        display position A → canonical option_c)
    """
    if not display_choice or shuffle_seed is None:
        return display_choice

    # Only deshuffle standard option keys
    if display_choice not in _CANONICAL_KEYS:
        return display_choice

    mapping = get_shuffle_mapping(shuffle_seed, round_number)
    return mapping["display_to_canonical"].get(display_choice, display_choice)


def strip_canonical_metadata(options: dict[str, Any]) -> dict[str, Any]:
    """
    Remove internal _canonical_key metadata before sending to frontend.
    """
    cleaned = {}
    for key, opt_data in options.items():
        if isinstance(opt_data, dict):
            cleaned_opt = {k: v for k, v in opt_data.items() if not k.startswith("_")}
            cleaned[key] = cleaned_opt
        else:
            cleaned[key] = opt_data
    return cleaned
