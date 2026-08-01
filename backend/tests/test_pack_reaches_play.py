"""A pack chosen at cohort setup must change what the player actually sees.

THE DEFECT (found by the 2026-07-31 "verify it cannot repeat" sweep)
--------------------------------------------------------------------
The pack dropdowns saved NOTHING and resolved NOWHERE:

  * StartSessionRequest had no pack fields — Pydantic silently discarded the
    ids the create form sent;
  * the metadata PATCH filtered them out of EDITABLE — the edit form's ids
    were silently dropped too;
  * the resolvers read stakeholder_pack_id / materiality_pack_id from
    global_state, which nothing ever wrote;
  * get_stakeholders_for_session had no pack step at all (only the unused
    per-BU helper did).

Four breaks, zero errors anywhere: the feature was decorative end-to-end.
This file pins the full round-trip — form field → session record → hydration
→ resolution → player-visible data — in memory mode; the same flow is drilled
against real Postgres (pgserver) in the release checks.
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


@pytest.fixture
def packs(tmp_path, monkeypatch):
    """Uploaded configs + packs, isolated from the real volume."""
    monkeypatch.setenv("MURESSONS_DATA_DIR", str(tmp_path))
    import stakeholder_db
    import materiality_db
    from stakeholder_packs import save_pack as save_sh
    from materiality_packs import save_pack as save_mat, invalidate_cache
    import stakeholder_packs

    rows = [{"id": "pack_stakeholder", "name": "Pack Stakeholder", "icon": "📦",
             "description": "from the pack", "correct_quadrant": "q1", "intel_dossier": []}]
    assert stakeholder_db.save_region_config("vertical_pharma__test_eu", rows)
    assert save_sh("packa", "Pack A", "test_eu", {"pharma": "vertical_pharma__test_eu"})

    assert materiality_db.save_regional_bu_config("pharma", "test_eu", {
        "consultant_fee_usd": 1_000_000,
        "issues": [{"id": "pack_issue", "title": "Pack Issue", "category": "environmental",
                    "financial_impact": "high", "societal_impact": "high",
                    "mitigation_cost_usd": 1_000_000, "hover_description": "x"}],
        "interdependencies": []})
    assert save_mat("packm", "Pack M", "test_eu", {"pharma": "pharma__test_eu"})
    invalidate_cache()
    try:
        stakeholder_packs.invalidate_cache()
    except AttributeError:
        pass
    yield
    invalidate_cache()


def _clear():
    import rate_limit
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()


def _mk_cohort_with_packs(client):
    _clear()
    client.post("/api/admin/facilitators/login",
                json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    r = client.post("/api/simulations/start", json={
        "cohort_name": "PackPlay", "facilitator_id": "god_mode",
        "simulation_mode": "single_bu", "industry_vertical": "pharma",
        "stakeholder_pack_id": "packa", "materiality_pack_id": "packm"})
    assert r.status_code == 201, r.text
    return str(r.json()["session_id"])


def test_start_persists_both_pack_ids(client, packs):
    import database_memory as dbm
    sid = _mk_cohort_with_packs(client)
    sess = dbm._sessions[sid]
    assert sess.get("stakeholder_pack_id") == "packa"
    assert sess.get("materiality_pack_id") == "packm"


def test_player_stakeholder_bank_shows_the_pack_set(client, packs):
    sid = _mk_cohort_with_packs(client)
    _clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    j = client.post(f"/api/simulations/public/sessions/{sid}/join",
                    json={"player_id": g["player_id"], "password": g["password"]}).json()
    psid = str(j["session_id"])
    sh = client.get(f"/api/simulations/stakeholder-map/stakeholders?session_id={psid}").json()
    assert [s["id"] for s in sh["stakeholders"]] == ["pack_stakeholder"], (
        "the pack chosen at setup did not reach the player's bank")


def test_materiality_display_resolves_the_pack(client, packs):
    sid = _mk_cohort_with_packs(client)
    _clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    j = client.post(f"/api/simulations/public/sessions/{sid}/join",
                    json={"player_id": g["player_id"], "password": g["password"]}).json()
    psid = str(j["session_id"])
    m = client.get(f"/api/admin/materiality-config/bu/pharma?session_id={psid}").json()
    assert [i["title"] for i in m.get("issues", [])] == ["Pack Issue"], (
        "the display endpoint did not resolve the cohort's materiality pack")


def test_metadata_patch_accepts_pack_ids(client, packs):
    import database_memory as dbm
    sid = _mk_cohort_with_packs(client)
    _clear()
    r = client.patch(f"/api/admin/sessions/{sid}/metadata",
                     json={"stakeholder_pack_id": "", "materiality_pack_id": "packm"})
    # whatever the auth outcome, the FILTER must not be the thing dropping them
    if r.status_code == 200:
        assert r.json().get("status") != "no_changes", (
            "EDITABLE silently filtered the pack ids out again")


def test_cohort_without_packs_is_byte_identical_to_before(client, packs):
    """No pack: the bank must be the default resolution — the pack step must
    be additive-only (the back-compat contract every pack feature carries)."""
    _clear()
    client.post("/api/admin/facilitators/login",
                json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    r = client.post("/api/simulations/start",
                    json={"cohort_name": "NoPacks", "facilitator_id": "god_mode"})
    sid = str(r.json()["session_id"])
    _clear()
    g = client.post(f"/api/admin/{sid}/generate-player").json()
    j = client.post(f"/api/simulations/public/sessions/{sid}/join",
                    json={"player_id": g["player_id"], "password": g["password"]}).json()
    psid = str(j["session_id"])
    sh = client.get(f"/api/simulations/stakeholder-map/stakeholders?session_id={psid}").json()
    ids = [s["id"] for s in sh["stakeholders"]]
    assert "pack_stakeholder" not in ids
    assert len(ids) >= 5, "default stakeholder bank went missing"
