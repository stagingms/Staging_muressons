"""Result-visibility enforcement on the player peer-leaderboard.

Server-side (not just UI) gating of the /peer-leaderboard endpoint:
  - results_reveal_round withholds the whole ranking until that round;
  - redact_peer_identities forces the anonymous team label for every peer but
    the requester;
  - both default OFF ⇒ byte-for-byte the previous behaviour (real names shown).
"""

import asyncio

import database_memory as dbm
from admin_shared import cohort_settings
from router import get_peer_leaderboard

_PARENT = "cohort-viz"
_A = "player-A"   # requester
_B = "player-B"
_C = "player-C"


def _setup(round_number=3):
    dbm._sessions[_PARENT] = {"parent_cohort_id": None, "player_name": "COHORT"}
    dbm._sessions[_A] = {"parent_cohort_id": _PARENT, "player_id": "pa", "player_name": "Alice Co"}
    dbm._sessions[_B] = {"parent_cohort_id": _PARENT, "player_id": "pb", "player_name": "Bob Co"}
    dbm._sessions[_C] = {"parent_cohort_id": _PARENT, "player_id": "pc", "player_name": "Cara Co"}
    for sid, treasury in ((_A, 30e6), (_B, 50e6), (_C, 10e6)):
        dbm._global_states[sid] = [{
            "corporate_treasury": treasury, "group_reputation": 55,
            "tco2e_emissions": 100, "bonus_score": 0,
            "round_number": round_number, "synergy_multiplier": 1.0,
        }]


def _teardown():
    for sid in (_PARENT, _A, _B, _C):
        dbm._sessions.pop(sid, None)
        dbm._global_states.pop(sid, None)
    cohort_settings.pop(_PARENT, None)


class _Req:
    """F-22: the route binds the caller to the session — present the requester's
    own signed player token (session _A is owned by player "pa")."""
    method = "GET"
    cookies = {}

    def __init__(self, sid):
        from conftest import player_token_headers
        self.headers = player_token_headers(sid, dbm._sessions[sid]["player_id"])


def _run(sid):
    # asyncio.run gives each call a fresh loop — robust when the shared loop has
    # been closed/replaced by other async tests earlier in the suite.
    return asyncio.run(get_peer_leaderboard(sid, _Req(sid)))


def test_default_shows_real_names_and_all_rounds():
    _setup(round_number=2)
    try:
        res = _run(_A)
        names = {e["name"] for e in res["leaderboard"]}
        assert res.get("locked") is not True
        # Default (redaction off): everyone's real name shows, incl. the requester.
        assert "Alice Co" in names
        assert "Bob Co" in names and "Cara Co" in names
    finally:
        _teardown()


def test_reveal_schedule_locks_before_the_round():
    _setup(round_number=3)
    cohort_settings[_PARENT] = {"results_reveal_round": 6}
    try:
        res = _run(_A)
        assert res.get("locked") is True
        assert res["reveal_round"] == 6
        assert res["leaderboard"] == []
    finally:
        _teardown()


def test_reveal_schedule_unlocks_at_the_round():
    _setup(round_number=6)
    cohort_settings[_PARENT] = {"results_reveal_round": 6}
    try:
        res = _run(_A)
        assert res.get("locked") is not True
        assert len(res["leaderboard"]) == 3
    finally:
        _teardown()


def test_redaction_anonymises_peers_but_not_you():
    _setup(round_number=4)
    cohort_settings[_PARENT] = {"redact_peer_identities": True}
    try:
        res = _run(_A)
        by_you = {e["isYou"]: e["name"] for e in res["leaderboard"]}
        # Requester still sees themselves…
        assert by_you[True] in ("Your Team", "Alice Co")
        # …but no peer's real name leaks.
        peer_names = [e["name"] for e in res["leaderboard"] if not e["isYou"]]
        assert "Bob Co" not in peer_names and "Cara Co" not in peer_names
        assert all(n.startswith("Team ") for n in peer_names)
    finally:
        _teardown()
