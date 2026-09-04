"""The graded exercise's answer keys and the facilitator's script are not
readable without credentials — audit 2026-09-04 F-10 / F-11 (ACC-1..3), WP-10.

WHAT LEAKED (all 200 with no cookie, no token — next.config.mjs proxies every
backend route to the public URL):
  • GET /api/admin/teleprompter[/{round}[/{paradigm}]] — the facilitator's
    per-round script, quoting each option's payoff ("Option A → +0.10 M_R …");
  • /simulation-reference, /engine-tunables, /scenario-presets,
    /flag-dependencies, /side-tracks/blueprints, /interventions/master,
    /pedagogical/debrief-protocol — every tuning constant and the flag graph;
  • GET /api/simulations/stakeholder-map/master — each stakeholder's
    correct_quadrant and per-tactic correct flags (the R1 answer key);
  • GET /api/admin/materiality-config[/bu/{bu}] — per issue financial_impact +
    societal_impact (= the correct quadrant) and panel_recommendations, whose
    `experts` column is always correct (the R2 answer key). REQUIRED by the
    player's R2 matrix, so it is projected, not gated; the per-group hints
    moved to an owner-bound endpoint that records the commission.
  • GET /api/admin/journey/r6-revelation — each option's impacts and the
    backfire payoff. Rendered by the player cockpit at R6, so projected.
  • GET /api/admin/analytics/player/{sid} trusted a plaintext X-Player-Id
    header and admitted any facilitator: a rival's committed decisions.
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
    import router as rmod
    rate_limit._rate_buckets.clear()
    rate_limit._persistent_bans.clear()
    getattr(rmod, "_commit_timestamps", {}).clear()


def _login_god(client):
    _clear()
    r = client.post("/api/admin/facilitators/login",
                    json={"facilitator_id": "god_mode", "password": "test-master-pw"})
    assert r.status_code == 200, r.text


def _anon(client):
    """A client with no cookie and no player token."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app, raise_server_exceptions=False)


def _cohort(client, name):
    r = client.post("/api/simulations/start", json={"cohort_name": name, "facilitator_id": "god_mode"})
    assert r.status_code == 201, r.text
    return str(r.json()["session_id"])


def _player(client, cohort):
    """A joined player who has set a personal password (the F-01 gate refuses
    play on the issued one): (session_id, player_id, token)."""
    _clear()
    g = client.post(f"/api/admin/{cohort}/generate-player").json()
    j = client.post(f"/api/simulations/public/sessions/{cohort}/join",
                    json={"player_id": g["player_id"], "password": g["password"]}).json()
    a = _anon(client)
    r = a.post("/api/simulations/change-password",
               json={"player_id": g["player_id"], "old_password": g["password"], "new_password": "Personal#2026"})
    assert r.status_code == 200, r.text[:200]
    _clear()
    r = a.post("/api/simulations/player-login", json={"player_id": g["player_id"], "password": "Personal#2026"})
    assert r.status_code == 200, r.text[:200]
    return str(r.json()["session_id"]), g["player_id"], r.json().get("player_token")


def _player_headers(pid, tok):
    h = {"X-Player-Id": pid}
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


# ── 1. the reference/answer-key routes are gated ───────────────────────────

_GATED = [
    "/api/admin/teleprompter",
    "/api/admin/teleprompter/2",
    "/api/admin/teleprompter/2/legacy_abc",
    "/api/admin/pedagogical/debrief-protocol",
    "/api/admin/simulation-reference",
    "/api/admin/interventions/master",
    "/api/admin/engine-tunables",
    "/api/admin/scenario-presets",
    "/api/admin/flag-dependencies",
    "/api/admin/side-tracks/blueprints",
    "/api/simulations/stakeholder-map/master",
]


@pytest.mark.parametrize("path", _GATED)
def test_reference_routes_refuse_anonymous_callers(client, path):
    r = _anon(client).get(path)
    assert r.status_code == 401, f"{path} answered {r.status_code} with no credentials: {r.text[:120]}"


@pytest.mark.parametrize("path", _GATED)
def test_reference_routes_still_serve_a_facilitator(client, path):
    _login_god(client)
    r = client.get(path)
    assert r.status_code == 200, f"{path} → {r.status_code} for a logged-in facilitator: {r.text[:120]}"
    assert len(r.content) > 20


def test_a_player_token_does_not_open_the_facilitator_script(client):
    """A player is authenticated, but not a facilitator."""
    _login_god(client)
    cohort = _cohort(client, "AnswerKeyGate")
    _, pid, tok = _player(client, cohort)
    r = _anon(client).get("/api/admin/teleprompter", headers=_player_headers(pid, tok))
    assert r.status_code == 401


# ── 2. the R2 matrix config is projected for players ───────────────────────

def test_materiality_config_hides_the_answer_key_from_players(client):
    r = _anon(client).get("/api/admin/materiality-config")
    assert r.status_code == 200, "the R2 matrix must still load for a player"
    body = r.json()
    assert body.get("player_projection") is True
    assert body.get("issues"), "issues are what the matrix renders"
    for issue in body["issues"]:
        for k in ("financial_impact", "societal_impact", "correct_quadrant"):
            assert k not in issue, f"issue {issue.get('id')} still carries {k}"
        assert issue.get("id") and issue.get("title"), "the tile fields survive"
    assert "panel_recommendations" not in body, "the experts column is the answer key"
    assert body.get("panel_group_config"), "the commission UI needs the group config"
    assert "consultant_fee_usd" in body


def test_bu_materiality_config_is_projected_too(client):
    import materiality_db as mat_db
    bu = mat_db.get_bu_ids()[0]
    r = _anon(client).get(f"/api/admin/materiality-config/bu/{bu}")
    assert r.status_code == 200
    body = r.json()
    assert body.get("player_projection") is True
    assert "panel_recommendations" not in body
    assert all("financial_impact" not in i for i in body["issues"])


def test_materiality_config_is_complete_for_a_facilitator(client):
    _login_god(client)
    body = client.get("/api/admin/materiality-config").json()
    assert "player_projection" not in body
    assert body.get("panel_recommendations")
    assert any("financial_impact" in i for i in body["issues"])


def test_commissioning_a_panel_serves_that_group_and_records_the_fee(client):
    """The hint mechanic still works: one group per call, owner-bound,
    recorded so the fee is charged at submission even if the client
    forgets to list it."""
    from round2_csrd import compute_panel_recommendations
    import materiality_db as mat_db
    _login_god(client)
    cohort = _cohort(client, "PanelCommission")
    psid, pid, tok = _player(client, cohort)
    hdr = _player_headers(pid, tok)
    a = _anon(client)

    # someone else's session / no token → refused
    r = a.post(f"/api/simulations/{psid}/materiality/commission-panel", json={"group": "experts"})
    assert r.status_code in (401, 403), r.text

    r = a.post(f"/api/simulations/{psid}/materiality/commission-panel", json={"group": "experts"}, headers=hdr)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["group"] == "experts" and d["commissioned"] == ["experts"]
    expected = compute_panel_recommendations(mat_db.get_current_config()["issues"])
    assert d["recommendations"] == {iid: g["experts"] for iid, g in expected.items()}
    # only the requested group's column
    assert all(isinstance(v, str) for v in d["recommendations"].values())

    # idempotent; a second group accumulates
    assert a.post(f"/api/simulations/{psid}/materiality/commission-panel", json={"group": "experts"}, headers=hdr).json()["commissioned"] == ["experts"]
    r = a.post(f"/api/simulations/{psid}/materiality/commission-panel", json={"group": "ngos"}, headers=hdr)
    assert r.json()["commissioned"] == ["experts", "ngos"]
    assert a.post(f"/api/simulations/{psid}/materiality/commission-panel", json={"group": "astrologers"}, headers=hdr).status_code == 422

    # recorded on the session (survives the fetch→update round-trip)
    import router as rmod
    import database as db
    from router import _commissioned_panels
    import anyio
    latest = anyio.run(db.fetch_latest_state, psid)
    assert _commissioned_panels(latest["global_state"]) == {"experts", "ngos"}
    # and they are not read as active flags
    assert not ({"experts", "ngos"} & rmod._collect_flags_from_state(latest["global_state"].get("active_event_flags", {})))

    # submission charges both groups although the client lists neither
    before = latest["global_state"]["corporate_treasury"]
    _clear()
    r = a.post(f"/api/simulations/{psid}/materiality", headers=hdr,
               json={"matrix_submission": {"quadrant_1_top_right": [], "quadrant_2_top_left": [],
                                           "quadrant_3_bottom_right": [], "quadrant_4_bottom_left": []},
                     "consultant_used": False, "panel_groups_commissioned": [],
                     "force_override_cfo": True})
    assert r.status_code == 200, r.text[:200]
    from round2_csrd import ROUND_2_DEFAULT_CONFIG
    groups = ROUND_2_DEFAULT_CONFIG["round_2_config"]["stakeholder_panel"]["groups"]
    fee = groups["experts"].get("fee_usd", 750_000) + groups["ngos"].get("fee_usd", 750_000)
    after = anyio.run(db.fetch_latest_state, psid)["global_state"]
    assert after.get("stakeholder_panel_fee_paid") == fee
    assert sorted(after.get("stakeholder_panel_groups_commissioned", [])) == ["experts", "ngos"]


# ── 3. the R6 revelation is projected for players ──────────────────────────

def test_r6_revelation_hides_payoffs_from_players(client):
    body = _anon(client).get("/api/admin/journey/r6-revelation").json()["revelation"]
    assert body.get("player_projection") is True
    assert body.get("title") and body.get("narrative") and body.get("micro_decisions")
    for key, dec in body["micro_decisions"].items():
        assert "impacts" not in dec and "flags_set" not in dec, key
        assert dec.get("label") and dec.get("description")
        if "stochastic" in dec:
            assert "backfire_probability" in dec["stochastic"]      # the panel shows it by design
            assert "backfire_impacts" not in dec["stochastic"]
    _login_god(client)
    full = client.get("/api/admin/journey/r6-revelation").json()["revelation"]
    assert "player_projection" not in full
    assert all("impacts" in d for d in full["micro_decisions"].values())


# ── 4. analytics/player binds the caller ───────────────────────────────────

def test_player_analytics_rejects_a_forged_header_and_a_rival(client):
    _login_god(client)
    cohort = _cohort(client, "AnalyticsGuard")
    a_sid, a_pid, a_tok = _player(client, cohort)
    b_sid, b_pid, b_tok = _player(client, cohort)
    anon = _anon(client)

    # the exact F-11 probe: B's session id + B's player id, no token
    r = anon.get(f"/api/admin/analytics/player/{b_sid}", headers={"X-Player-Id": b_pid})
    assert r.status_code in (401, 403), f"forged header still reads a rival: {r.status_code}"
    # A's real token against B's session
    r = anon.get(f"/api/admin/analytics/player/{b_sid}", headers=_player_headers(a_pid, a_tok))
    assert r.status_code == 403, r.text[:120]
    # B reads B (the PlayerAnalytics panel)
    r = anon.get(f"/api/admin/analytics/player/{b_sid}", headers=_player_headers(b_pid, b_tok))
    assert r.status_code == 200, r.text[:160]
    # the owning facilitator reads it
    assert client.get(f"/api/admin/analytics/player/{b_sid}").status_code == 200


def test_player_analytics_refuses_a_facilitator_from_another_cohort(client):
    _login_god(client)
    cohort = _cohort(client, "AnalyticsTenancy")
    b_sid, _, _ = _player(client, cohort)
    # a plain facilitator who owns nothing (plaintext password: the login
    # path accepts it and upgrades it to bcrypt on success)
    from admin_shared import _facilitator_registry
    pw = "Other#2026pw"
    rec = {"facilitator_id": "FAC-OTHER-ANALYTICS", "name": "Other", "username": "other",
           "password": pw, "role": "facilitator", "enabled": True}
    _facilitator_registry.append(rec)
    try:
        other = _anon(client)
        r = other.post("/api/admin/facilitators/login", json={"facilitator_id": rec["facilitator_id"], "password": pw})
        assert r.status_code == 200, r.text[:200]
        r = other.get(f"/api/admin/analytics/player/{b_sid}")
        assert r.status_code == 403, f"another cohort's facilitator read a team's analytics: {r.status_code}"
    finally:
        _facilitator_registry[:] = [f for f in _facilitator_registry if f.get("facilitator_id") != rec["facilitator_id"]]


# ── 5. source pins ─────────────────────────────────────────────────────────

def test_analytics_guard_is_not_a_header_compare():
    import inspect
    import admin_analytics
    src = inspect.getsource(admin_analytics.get_player_analytics)
    assert 'request.headers.get("X-Player-Id"' not in src
    assert "_assert_player_owns_session(request, session_id" in src
    assert "_assert_session_visible(request, session_id)" in src
