"""A cohort freeze must stop THAT cohort, and only that cohort (2026-09-03).

WHAT THIS PINS
    `system_frozen` is in admin_shared.COHORT_OVERRIDABLE_KEYS, and
    admin_router grants a lead_facilitator write access to it for cohorts they
    own. But the ONLY enforcement point — the freeze guard in
    router._commit_turn_impl — read the process-global `_god_mode_settings`.

    So the flag had exactly two behaviours, both wrong:
      * a lead facilitator freezing their own cohort got a 200, saw it applied
        on the settings screen, and their class carried on committing;
      * a super-admin freeze stopped all thirty classes at once.

    The guard now reads get_effective_settings(session_id) as well, and EITHER
    freeze applies: a cohort can stop itself, but cannot escape a platform-wide
    maintenance freeze with a stale override.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app
from conftest import rotate_facilitator_password

client = TestClient(app)
GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}


_MISSING = object()


@pytest.fixture(autouse=True)
def _clean_freeze_state():
    """Never leave a freeze behind — it would 503 every later test.

    RESTORE, do not pop. `system_frozen` is a platform default that ships as
    False, and test_medium_cohort_controls asserts `eff["system_frozen"] is
    False` — popping the key made that a KeyError. Snapshot the original value
    (including "absent") and put exactly that back.
    """
    import admin_shared
    original = admin_shared._god_mode_settings.get("system_frozen", _MISSING)

    def _restore():
        if original is _MISSING:
            admin_shared._god_mode_settings.pop("system_frozen", None)
        else:
            admin_shared._god_mode_settings["system_frozen"] = original

    _restore()
    touched: list[str] = []
    yield touched
    _restore()
    for sid in touched:
        admin_shared.cohort_settings.pop(sid, None)


def _god():
    return client.post("/api/admin/facilitators/login", json=GOD).cookies


def _cohort(ck, name):
    r = client.post("/api/simulations/start",
                    json={"cohort_name": name, "facilitator_id": "god_mode"}, cookies=ck)
    assert r.status_code in (200, 201), r.text
    return r.json()["session_id"]


def _team(ck, cohort, name="Team"):
    """generate-player + player-login -> (player_id, sub_session_id, headers).
    Mirrors test_launch_audit_2026_09_01._team; the token key is `player_token`."""
    # Retry on 409 player_id_ambiguous. That is F-40's deliberate refusal when
    # the same id AND default password exist in more than one cohort, and in a
    # FULL suite run enough cohorts exist for it to happen. It has nothing to do
    # with freezing, so a fresh id is the right response rather than a failure
    # here — this test must fail for freeze reasons only.
    for _attempt in range(5):
        g = client.post(f"/api/admin/{cohort}/generate-player",
                        json={"player_name": f"{name}-{_attempt}"}, cookies=ck)
        assert g.status_code in (200, 201), g.text
        pid, pw = g.json()["player_id"], g.json()["password"]
        client.cookies.clear()
        lr = client.post("/api/simulations/player-login",
                         json={"player_id": pid, "password": pw})
        if lr.status_code == 200:
            break
        assert lr.status_code == 409 and "ambiguous" in lr.text, lr.text
        client.cookies = ck
    assert lr.status_code == 200, lr.text
    body = lr.json()
    assert body.get("player_token"), "login must mint a signed player token (F-22)"
    assert client.post("/api/simulations/change-password",
                       json={"player_id": pid, "old_password": pw,
                             "new_password": f"frz-{pid}-1"}).status_code == 200
    return pid, body["session_id"], {"Authorization": f"Bearer {body['player_token']}",
                                     "X-Player-Id": pid}


def _payload(team, H):
    dash = client.get(f"/api/simulations/{team}/dashboard", headers=H).json()
    assert "business_units" in dash, f"dashboard shape: {sorted(dash)[:12]}"
    return {
        "decisions": [{"bu_id": b["bu_id"], "capex_allocated": 1,
                       "choice_selected": "option_b"} for b in dash["business_units"]],
        "expected_round": dash["current_round"],
    }


def test_a_global_freeze_is_refused_end_to_end(_clean_freeze_state):
    """A 503 here can only be the freeze guard: the SAME payload is accepted
    first, so a malformed body cannot masquerade as a freeze."""
    import admin_shared
    from router import _commit_timestamps
    gm = _god()
    cohort = _cohort(gm, "Freeze E2E global")
    _clean_freeze_state.append(cohort)
    _pid, team, H = _team(gm, cohort, "T1")

    _commit_timestamps.pop(team, None)
    ok = client.post(f"/api/simulations/{team}/commit-turn",
                     json=_payload(team, H), headers=H)
    assert ok.status_code == 201, f"payload not otherwise valid: {ok.status_code} {ok.text[:200]}"

    admin_shared._god_mode_settings["system_frozen"] = True
    _commit_timestamps.pop(team, None)
    r = client.post(f"/api/simulations/{team}/commit-turn",
                    json=_payload(team, H), headers=H)
    assert r.status_code == 503, f"frozen system must refuse: {r.status_code} {r.text[:200]}"
    assert "frozen" in r.text.lower(), r.text


def test_a_cohort_freeze_is_refused_end_to_end(_clean_freeze_state):
    """The half that was broken. Freeze the PARENT cohort, commit as the PLAYER
    sub-session — the guard has to resolve one to the other."""
    import admin_shared
    from router import _commit_timestamps
    gm = _god()
    cohort = _cohort(gm, "Freeze E2E cohort")
    _clean_freeze_state.append(cohort)
    _pid, team, H = _team(gm, cohort, "T2")

    _commit_timestamps.pop(team, None)
    ok = client.post(f"/api/simulations/{team}/commit-turn",
                     json=_payload(team, H), headers=H)
    assert ok.status_code == 201, f"payload not otherwise valid: {ok.status_code} {ok.text[:200]}"

    admin_shared.cohort_settings.setdefault(cohort, {})["system_frozen"] = True
    admin_shared.cohort_settings[cohort]["freeze_message"] = "Debrief in progress"
    _commit_timestamps.pop(team, None)
    r = client.post(f"/api/simulations/{team}/commit-turn",
                    json=_payload(team, H), headers=H)
    assert r.status_code == 503, (
        f"a cohort freeze did not stop its own cohort's commit ({r.status_code}). "
        f"The guard must resolve the player sub-session up to its parent cohort.")
    assert "Debrief in progress" in r.text, r.text


def test_an_unfrozen_neighbour_cohort_still_commits(_clean_freeze_state):
    """The other half: one cohort's freeze must not stop anybody else."""
    import admin_shared
    from router import _commit_timestamps
    gm = _god()
    frozen_c = _cohort(gm, "Freeze neighbour A")
    other_c = _cohort(gm, "Freeze neighbour B")
    _clean_freeze_state.extend([frozen_c, other_c])
    _p1, team_frozen, H1 = _team(gm, frozen_c, "N1")
    _p2, team_other, H2 = _team(gm, other_c, "N2")

    admin_shared.cohort_settings.setdefault(frozen_c, {})["system_frozen"] = True

    _commit_timestamps.pop(team_frozen, None)
    r1 = client.post(f"/api/simulations/{team_frozen}/commit-turn",
                     json=_payload(team_frozen, H1), headers=H1)
    assert r1.status_code == 503, "the frozen cohort should be refused"

    _commit_timestamps.pop(team_other, None)
    r2 = client.post(f"/api/simulations/{team_other}/commit-turn",
                     json=_payload(team_other, H2), headers=H2)
    assert r2.status_code == 201, (
        f"a neighbouring cohort was blocked by another cohort's freeze "
        f"({r2.status_code}) — the freeze is not scoped")


def test_a_cohort_override_cannot_escape_a_platform_freeze(_clean_freeze_state):
    """EITHER freeze applies. A stale per-cohort `system_frozen: False` must not
    let a class keep playing straight through a platform maintenance freeze."""
    import admin_shared
    from router import _commit_timestamps
    gm = _god()
    cohort = _cohort(gm, "Freeze escape")
    _clean_freeze_state.append(cohort)
    _pid, team, H = _team(gm, cohort, "E1")

    _commit_timestamps.pop(team, None)
    ok = client.post(f"/api/simulations/{team}/commit-turn",
                     json=_payload(team, H), headers=H)
    assert ok.status_code == 201, f"payload not otherwise valid: {ok.status_code}"

    admin_shared._god_mode_settings["system_frozen"] = True
    admin_shared.cohort_settings.setdefault(cohort, {})["system_frozen"] = False
    _commit_timestamps.pop(team, None)
    r = client.post(f"/api/simulations/{team}/commit-turn",
                    json=_payload(team, H), headers=H)
    assert r.status_code == 503, (
        f"a per-cohort override escaped a platform-wide freeze ({r.status_code})")
