"""The roster cap must honour the control the facilitator actually used.

BUG-2026-07-29 (audit). `resolve_roster_cap` read ONLY `team_count`. The
`max_players` control — named for roster size, clamped to MAX_PLAYERS_CEILING
(20), and the whole point of the "up to 20 players per cohort" work — was
silently inert:

    PATCH cohort-settings {"max_players": 20}   -> 200 OK, saved
    resolve_roster_cap(cohort)                  -> 5
    6th student joins                           -> 400 "roster cap of 5 player(s)"

The save succeeded and the setting read back correctly; only the join gate
disagreed. Nothing surfaced the mismatch until students were already in the
room and the 6th one could not get in — the worst possible moment.

Both knobs now raise the cap and the LARGER wins, so setting either does what
the facilitator meant, and a stale low value in one field cannot silently
shrink a roster the other widened.
"""
import os
import pathlib
import tempfile

import pytest


@pytest.fixture(scope="module")
def client():
    d = tempfile.mkdtemp(prefix="rostercap_")
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


def _cohort(client, patch=None):
    sid = str(client.post("/api/simulations/start",
                          json={"cohort_name": "RC-" + os.urandom(4).hex(),
                                "facilitator_id": "god_mode"}
                          ).json()["session_id"])
    if patch:
        r = client.patch(f"/api/admin/sessions/{sid}/cohort-settings", json=patch)
        assert r.status_code == 200, r.text
    return sid


@pytest.mark.parametrize("patch,expected,why", [
    # 2026-07-31 (facilitator request): the unconfigured default rose 5 → 20
    # (the ceiling) so a forgotten max_players cannot bounce the 6th student.
    (None,                            20, "unconfigured cohort gets the full platform ceiling"),
    ({"max_players": 20},             20, "THE BUG: max_players was accepted and ignored"),
    ({"team_count": 20},              20, "team_count still works (no regression)"),
    ({"team_count": 8},               8,  "a smaller team_count is honoured exactly"),
    ({"team_count": 8, "max_players": 20}, 20, "larger wins — never silently shrink a roster"),
    ({"max_players": 999},            20, "clamped to MAX_PLAYERS_CEILING"),
])
def test_roster_cap_resolution(client, patch, expected, why):
    from admin_shared import resolve_roster_cap
    sid = _cohort(client, patch)
    assert resolve_roster_cap(sid) == expected, why


def test_twenty_players_can_actually_join(client):
    """The end the facilitator cares about: 20 students, 20 seats.

    Resolution alone is not proof — the join endpoint reads the cap through
    its own import path, which is exactly where the original defect lived."""
    from rate_limit import _rate_buckets, _persistent_bans
    sid = _cohort(client, {"max_players": 20})
    joined = 0
    for i in range(20):
        _rate_buckets.clear()
        _persistent_bans.clear()
        g = client.post(f"/api/admin/{sid}/generate-player")
        assert g.status_code == 200, f"player {i+1} could not be generated: {g.text}"
        gj = g.json()
        j = client.post(f"/api/simulations/public/sessions/{sid}/join",
                        json={"player_id": gj["player_id"], "password": gj["password"]})
        assert j.status_code == 200, (
            f"student #{i+1} of 20 was refused: {j.text}. A cohort configured "
            "for 20 must seat 20."
        )
        joined += 1
    assert joined == 20


def test_cap_is_still_enforced_past_the_limit(client):
    """Raising the cap must not remove it — an unbounded roster would let a
    stray link pull the whole school into one cohort."""
    from rate_limit import _rate_buckets, _persistent_bans
    sid = _cohort(client, {"max_players": 2})
    for _ in range(2):
        _rate_buckets.clear()
        _persistent_bans.clear()
        gj = client.post(f"/api/admin/{sid}/generate-player").json()
        client.post(f"/api/simulations/public/sessions/{sid}/join",
                    json={"player_id": gj["player_id"], "password": gj["password"]})
    _rate_buckets.clear()
    _persistent_bans.clear()
    # The cap is enforced at BOTH ends — generation refuses to mint a 3rd id,
    # and the join gate would refuse it anyway. Either rejection is correct;
    # what must never happen is a 3rd seat in a cohort configured for 2.
    g = client.post(f"/api/admin/{sid}/generate-player")
    if g.status_code == 200 and "player_id" in g.json():
        gj = g.json()
        j = client.post(f"/api/simulations/public/sessions/{sid}/join",
                        json={"player_id": gj["player_id"], "password": gj["password"]})
        assert j.status_code == 400, "the 3rd player joined a cohort capped at 2"
        assert "roster cap" in j.text.lower()
    else:
        assert g.status_code in (400, 403, 409), (
            f"generation of the 3rd id neither succeeded nor was cleanly "
            f"refused: {g.status_code} {g.text[:120]}"
        )
