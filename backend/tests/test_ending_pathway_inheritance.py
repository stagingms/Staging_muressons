"""A player must play the ending the facilitator chose for the cohort.

THE DEFECT (found by the pre-class 5-endings drill, 2026-07-31)
----------------------------------------------------------------
/start writes the cohort's chosen (or 'random'-resolved) pathway onto the
COHORT's round flags — but a player's child session is created by the join
flow, whose create_session call never received it: the memory backend seeded
the child from the GLOBAL default ('activist_ultimatum') and Postgres seeded
nothing. The round-10 finale reads the PLAYER session's flag, so every
player played Activist Ultimatum regardless of the facilitator's choice —
including 'random', which resolved correctly on the cohort and was then
ignored. Full 10-round drills confirmed: all five pathways requested, all
five finished as activist_ultimatum.

The fix copies the cohort's resolved flag onto the child at join. It must
write BOTH the flag and the top-level key: the memory round carries a
top-level ending_pathway and the persist repack prefers top-level values, so
a flags-only write was silently overwritten (verified step-by-step).
"""
import pytest


@pytest.fixture
def client(monkeypatch):
    import master_credentials
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app, raise_server_exceptions=False)


def _clear():
    import rate_limit
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()


def _join_one(client, pathway):
    _clear()
    client.post("/api/admin/facilitators/login",
                json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    r = client.post("/api/simulations/start",
                    json={"cohort_name": f"EP-{pathway}", "facilitator_id": "god_mode",
                          "ending_pathway": pathway})
    assert r.status_code == 201, r.text
    sid = str(r.json()["session_id"])
    _clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    j = client.post(f"/api/simulations/public/sessions/{sid}/join",
                    json={"player_id": g["player_id"], "password": g["password"]})
    assert j.status_code == 200, j.text
    return sid, str(j.json()["session_id"])


@pytest.mark.parametrize("pathway", [
    "activist_ultimatum", "climate_black_swan", "stakeholder_revolt",
    "hostile_takeover", "regulatory_shutdown",
])
def test_child_session_inherits_the_cohort_pathway(client, pathway):
    import database_memory as dbm
    _sid, psid = _join_one(client, pathway)
    row = dbm._global_states[psid][-1]
    flag = (row.get("active_event_flags") or {}).get("ending_pathway")
    assert flag == pathway, (
        f"player session plays '{flag}' but the facilitator chose '{pathway}' — "
        "the class would see the wrong (or always the same) ending")
    # and the top-level copy agrees, so the persist repack cannot revert it
    assert row.get("ending_pathway", pathway) == pathway


def test_random_resolves_once_per_cohort_and_children_follow_it(client):
    """'random' must resolve at COHORT creation; every player then inherits
    the SAME concrete pathway (one classroom narrative per cohort)."""
    import database_memory as dbm
    from ending_pathways import ALL_PATHWAY_IDS
    _clear()
    client.post("/api/admin/facilitators/login",
                json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    r = client.post("/api/simulations/start",
                    json={"cohort_name": "EP-random", "facilitator_id": "god_mode",
                          "ending_pathway": "random"})
    sid = str(r.json()["session_id"])
    cohort_ep = (dbm._global_states[sid][-1].get("active_event_flags") or {}).get("ending_pathway")
    assert cohort_ep in ALL_PATHWAY_IDS, "random did not resolve to a concrete pathway"

    child_eps = set()
    for _ in range(2):
        _clear()
        g = client.post(f"/api/admin/{sid}/generate-player").json()
        j = client.post(f"/api/simulations/public/sessions/{sid}/join",
                        json={"player_id": g["player_id"], "password": g["password"]})
        psid = str(j.json()["session_id"])
        child_eps.add((dbm._global_states[psid][-1].get("active_event_flags") or {}).get("ending_pathway"))
    assert child_eps == {cohort_ep}, (
        f"children diverged from the cohort's resolved random pathway: {child_eps} != {cohort_ep}")
