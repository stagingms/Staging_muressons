"""Tripwire: the three player-creation paths must produce the SAME record.

There are three ways a player record comes into existence:

    induct_player          — one player, typed in by a facilitator
    generate_player_id     — one anonymous id, no demographics yet
    _create_players_bulk   — many players, from a spreadsheet

They are separate functions on purpose (different guards, different capacity
sources, different batching), but the record they write is read by ONE set of
consumers: player-login, join, the roster projection and the dashboard. A
field added to one path and forgotten in the others is invisible in review and
shows up later as a player who cannot log in, or a column that is blank for
half a cohort.

This test parses the three record literals out of the source and fails on
drift. It is deliberately source-parsing rather than behavioural: calling the
endpoints needs a live app and would not notice a field that is present but
never populated.
"""
import pathlib
import re

import pytest

SRC = (pathlib.Path(__file__).resolve().parents[1] / "admin_router.py").read_text(encoding="utf-8")

# Fields every path must write. `programme` is here because it is optional to
# the AUTHOR, not to the RECORD — a missing key and an empty string are
# different things to a consumer doing rp["programme"].
REQUIRED = {
    "player_id", "name", "email", "programme", "assigned_bu", "session_id",
    "password", "plaintext_password", "must_change_password", "created_at", "status",
}


def _record_literal(anchor: str) -> set[str]:
    """Return the keys of the dict literal that follows `anchor`."""
    i = SRC.index(anchor)
    chunk = SRC[i:i + 2000]
    start = chunk.index("{")
    depth, end = 0, None
    for j, ch in enumerate(chunk[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = j
                break
    assert end is not None, f"unbalanced dict literal after {anchor!r}"
    return set(re.findall(r'"([a-z_0-9]+)":', chunk[start:end]))


@pytest.mark.parametrize("label,anchor", [
    ("induct_player", "    player = {\n        \"player_id\": generated_id,"),
    ("generate_player_id", "    player_entry = {\n        \"player_id\": player_id,"),
    ("_create_players_bulk", "        player = {\n            \"player_id\": pid,"),
])
def test_every_creation_path_writes_the_full_record(label, anchor):
    keys = _record_literal(anchor)
    missing = REQUIRED - keys
    assert not missing, f"{label} is missing {sorted(missing)}"


def test_no_path_stores_a_password_it_cannot_erase():
    """plaintext_password is only defensible because change_password deletes
    it. If that deletion is ever removed, the reveal policy silently becomes
    'staff can read personal passwords forever' — which the owner explicitly
    did not choose."""
    router = (pathlib.Path(__file__).resolve().parents[1] / "router.py").read_text(encoding="utf-8")
    i = router.index("async def change_password")
    body = router[i:i + 3000]
    assert 'player.pop("plaintext_password", None)' in body
    assert 'rp.pop("plaintext_password", None)' in body


def test_roster_projection_is_an_allow_list():
    """A deny-list would leak any field added later. Assert the projection
    builds from an explicit tuple and never ships the hash."""
    i = SRC.index("_ROSTER_PUBLIC_FIELDS")
    block = SRC[i:i + 1200]
    assert "password" not in _record_literal_fields(block), "hash must never be projected"
    assert "temp_password" in block


def _record_literal_fields(block: str) -> set[str]:
    m = re.search(r"_ROSTER_PUBLIC_FIELDS\s*=\s*\((.*?)\)", block, re.S)
    assert m, "could not find the projection tuple"
    return set(re.findall(r'"([a-z_0-9]+)"', m.group(1)))


def test_capacity_is_never_a_literal_again():
    """The cap was a hardcoded 10 at two sites that had to be kept in step by
    hand. Both now go through the resolver; a re-introduced literal is a bug."""
    assert "maximum of 10 players" not in SRC
    assert SRC.count("resolve_max_players(get_effective_settings(") >= 2
