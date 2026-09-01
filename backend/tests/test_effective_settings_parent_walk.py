"""Per-cohort settings must resolve for a PLAYER's sub-session id.

Reported: "the stakeholder negotiation room is not functional."

Nothing about the negotiation engine was broken — rooms open, transcripts
accumulate, concessions price and commit. Two things kept it away from
players, and this file pins the server-side one.

When a player joins a cohort they get their OWN sub-session, whose id is what
every player-side request carries. That sub-session never held the cohort's
overrides, so `get_effective_settings(player_session_id)` silently fell all
the way back to the PLATFORM default. The facilitator would enable Negotiation
Rooms, see it saved on the cohort, and the player would still get
403 "not enabled for this cohort" — because the gate was evaluated with the
child id, which knew nothing about the parent.

`resolve_analytics_visibility` already walked up to the parent cohort; this
did not. The asymmetry is the bug. Every per-cohort key is affected, not just
this one, so the tests below check a second unrelated key too.
"""
import os
import pathlib
import tempfile

import pytest


@pytest.fixture(scope="module")
def client():
    d = tempfile.mkdtemp(prefix="effsettings_")
    os.environ["MURESSONS_DATA_DIR"] = d
    pathlib.Path(d, "memory_snapshot.json").write_text("{}", encoding="utf-8")
    pathlib.Path(d, "facilitators.json").write_text("[]", encoding="utf-8")
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        r = c.post("/api/admin/facilitators/login",
                   json={"facilitator_id": "god_mode", "password": "sim2026@iim"})
        assert r.status_code == 200, r.text
        yield c


# NOT module-scoped: conftest's autouse clear_memory_db() empties _sessions
# before EVERY test, which would erase the parent link this file is about and
# make the tests fail for a reason that has nothing to do with the code.
@pytest.fixture
def cohort(client):
    """A cohort with one joined player. Returns (parent_id, child_id, player_id)."""
    import database_memory as dm
    from rate_limit import _rate_buckets, _persistent_bans
    sid = str(client.post("/api/simulations/start",
                          json={"cohort_name": "EffSettings-" + os.urandom(4).hex(),
                                "facilitator_id": "god_mode"}
                          ).json()["session_id"])
    _rate_buckets.clear()
    _persistent_bans.clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    client.post(f"/api/simulations/public/sessions/{sid}/join",
                json={"player_id": g["player_id"], "password": g["password"]})
    child = next(s for s, v in dm._sessions.items()
                 if v.get("parent_cohort_id") == sid)
    assert child != sid, "the player must get their own sub-session"
    return sid, child, g["player_id"]


def test_child_session_inherits_the_cohort_override(client, cohort):
    """The exact failure: enabled on the parent, invisible from the child."""
    from admin_shared import get_effective_settings
    parent, child, _ = cohort

    # Platform default is ON since 2026-09-01 (EVAL rec 2), so the walk is
    # proven with an OFF override: parent disables, child must see it.
    assert get_effective_settings(child).get("negotiation_rooms_enabled") is True

    r = client.patch(f"/api/admin/sessions/{parent}/cohort-settings",
                     json={"negotiation_rooms_enabled": False})
    assert r.status_code == 200, r.text

    assert get_effective_settings(parent).get("negotiation_rooms_enabled") is False
    assert get_effective_settings(child).get("negotiation_rooms_enabled") is False, (
        "the player's sub-session did not inherit the cohort override — every "
        "gate evaluated with a player session id resolves to the platform "
        "default, which is how the negotiation room originally stayed 403"
    )


def test_the_parent_walk_is_not_specific_to_one_key(client, cohort):
    """Any COHORT_OVERRIDABLE_KEYS entry, not a special case for negotiation
    rooms — the walk happens before any key is looked at.

    (Note the scope: pedagogy toggles like real_world_cards_enabled live in a
    separate `pedagogical_overrides` bucket with its own resolution path, so
    they are deliberately not what this asserts.)"""
    from admin_shared import COHORT_OVERRIDABLE_KEYS, get_effective_settings
    parent, child, _ = cohort
    assert "decision_timer_enabled" in COHORT_OVERRIDABLE_KEYS
    r = client.patch(f"/api/admin/sessions/{parent}/cohort-settings",
                     json={"decision_timer_enabled": True,
                           "decision_timer_seconds": 240})
    assert r.status_code == 200, r.text
    eff = get_effective_settings(child)
    assert eff.get("decision_timer_enabled") is True
    assert eff.get("decision_timer_seconds") == 240


def test_global_settings_endpoint_is_cohort_effective_for_a_player(client, cohort):
    """The cockpit fetches /global-settings?session_id=<its own id> — which is
    the CHILD id. If that response is not cohort-effective the entry point
    never renders, no matter what the server would allow."""
    parent, child, _ = cohort
    client.patch(f"/api/admin/sessions/{parent}/cohort-settings",
                 json={"negotiation_rooms_enabled": True})
    d = client.get(f"/api/admin/global-settings?session_id={child}").json()
    assert d.get("negotiation_rooms_enabled") is True


def test_unknown_session_id_still_returns_platform_defaults(client):
    """Fail open, not closed. A stale or bogus id must not raise."""
    from admin_shared import get_effective_settings
    d = get_effective_settings("no-such-session-id")
    assert isinstance(d, dict) and d, "must fall back to the global view"


def test_player_can_open_a_room_once_the_cohort_enables_it(client, cohort):
    """End to end through the real gate, with the player's own credentials."""
    import asyncio
    import database_memory as dm
    parent, child, player_id = cohort
    client.patch(f"/api/admin/sessions/{parent}/cohort-settings",
                 json={"negotiation_rooms_enabled": True})

    async def _make_hostile():
        st = await dm.fetch_latest_state(child)
        gs = st["global_state"]
        gs["autonomous_agents"] = {"agents": {
            "the_community_activist": {"escalation_stage": "hostile", "tolerance": 20}
        }}
        await dm.update_latest_global_state(child, gs, st["bu_states"])

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_make_hostile())
    finally:
        loop.close()

    r = client.post(f"/api/simulations/{child}/negotiation/open",
                    json={"agent_id": "the_community_activist"},
                    headers={"X-Player-Id": player_id})
    assert r.status_code == 200, f"player still cannot open a room: {r.text}"
    assert (r.json().get("room") or {}).get("agent_id") == "the_community_activist"
