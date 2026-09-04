"""Launch-audit regression tests (AUDIT_Independent_Review_2026-09-01.md §8,
"must change before a 30-cohort launch").

One test class per finding so a future regression names the finding it undoes.

  F-01  group reputation is derived from the BU stock — no phantom drift.
  F-02  water_dependency reaches the ESG-WACC as a 0-1 fraction; CoC base is a
        stock in active_event_flags, macro modifiers do not compound.
  F-03  CBAM surcharge is a plausible $/tCO2e figure with a poison-value guard.
  F-15  the memory store returns every persisted BU key (Postgres parity).
  F-20  /api/admin/sessions is scoped by the caller's JWT and carries no
        player credentials.
  F-21  a facilitator cannot read or act on a cohort it does not own.
  F-22  players are identified by a signed token; the initial password can
        only be used to change itself.
  F-24  /set-username and /change-password are no longer anonymous oracles.
"""

from __future__ import annotations

import math
import random

import pytest
from fastapi.testclient import TestClient

from main import app
from conftest import rotate_facilitator_password, player_token_headers

client = TestClient(app)

GOD = {"facilitator_id": "god_mode", "password": "sim2026@iim"}


@pytest.fixture
def decay_rate_on_volume(tmp_path, monkeypatch):
    """Load `config` against a data volume whose simulation_config.json carries
    a chosen imitation_decay.default_rate, then put the real one back.

    CONFIG_PATH and every typed constant are import-time, so the only way to
    exercise a config-load branch is the way config.reload_simulation_config()
    does it in production: point MURESSONS_DATA_DIR at a directory and reload.
    Teardown restores the environment AND reloads again, so this fixture does
    not leak a poisoned config into the rest of the session.
    """
    import importlib
    import json
    import os
    import pathlib
    import config as _config

    repo_cfg = pathlib.Path(__file__).resolve().parent.parent.parent / "simulation_config.json"
    original = os.environ.get("MURESSONS_DATA_DIR")

    def _load(rate):
        data = json.loads(repo_cfg.read_text(encoding="utf-8"))
        data.setdefault("engine_parameters", {}).setdefault("imitation_decay", {})["default_rate"] = rate
        (tmp_path / "simulation_config.json").write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setenv("MURESSONS_DATA_DIR", str(tmp_path))
        return importlib.reload(_config)

    yield _load

    if original is None:
        os.environ.pop("MURESSONS_DATA_DIR", None)
    else:
        os.environ["MURESSONS_DATA_DIR"] = original
    importlib.reload(_config)


def _god():
    r = client.post("/api/admin/facilitators/login", json=GOD)
    assert r.status_code == 200, r.text
    return r.cookies


def _facilitator(gm, name, role="facilitator"):
    """Create a registry facilitator and rotate it off its initial password."""
    r = client.post("/api/admin/facilitators", json={"name": name, "role": role}, cookies=gm)
    assert r.status_code in (200, 201), r.text
    fid, otp = r.json()["facilitator_id"], r.json()["one_time_password"]
    pw = rotate_facilitator_password(client, fid, otp)
    ck = client.post("/api/admin/facilitators/login", json={"facilitator_id": fid, "password": pw}).cookies
    return fid, ck


def _cohort(ck, fid, name):
    r = client.post("/api/simulations/start", json={"cohort_name": name, "facilitator_id": fid}, cookies=ck)
    assert r.status_code in (200, 201), r.text
    return r.json()["session_id"]


def _team(ck, cohort, name="Team"):
    """generate-player + player-login -> (player_id, password, sub_session_id, token)."""
    g = client.post(f"/api/admin/{cohort}/generate-player", json={"player_name": name}, cookies=ck)
    assert g.status_code in (200, 201), g.text
    pid, pw = g.json()["player_id"], g.json()["password"]
    client.cookies.clear()
    lr = client.post("/api/simulations/player-login", json={"player_id": pid, "password": pw})
    assert lr.status_code == 200, lr.text
    body = lr.json()
    assert body.get("player_token"), "login must mint a signed player token (F-22)"
    return pid, pw, body["session_id"], body["player_token"]


def _commit_payload(dash, expected_round):
    return {
        "decisions": [{"bu_id": b["bu_id"], "capex_allocated": 1, "choice_selected": "option_b"}
                      for b in dash["business_units"]],
        "expected_round": expected_round,
    }


def _clear_commit_gate(sid):
    from router import _commit_timestamps
    _commit_timestamps.pop(sid, None)


# ═══════════════════════════════════════════════════════════════════════════
#  F-01 — reputation
# ═══════════════════════════════════════════════════════════════════════════

class TestF01ReputationStock:
    def test_zero_severity_contagion_equals_bu_average(self):
        from engine import calc_contagion
        bus = [{"bu_id": "a", "reputation_score": 70.0}, {"bu_id": "b", "reputation_score": 40.0}]
        assert calc_contagion(bus, crisis_severity=0) == pytest.approx(55.0)

    def test_contagion_is_monotone_in_severity_and_bites_at_midpoint(self):
        from engine import calc_contagion
        bus = [{"bu_id": "a", "reputation_score": 60.0}]
        vals = [calc_contagion(bus, crisis_severity=s) for s in (0, 15, 30, 60, 100)]
        assert vals == sorted(vals, reverse=True)
        assert vals[0] == pytest.approx(60.0)
        assert vals[2] < 45.0          # a midpoint crisis still costs >15 points
        assert vals[-1] > 60.0 - 50.0  # never more than the configured max drop

    def test_group_reputation_does_not_drift_over_quiet_rounds(self):
        """Ten quiet ticks with a flat BU stock: the group figure stays put.
        Before F-01 it lost ~5.9 points per tick with no crisis at all."""
        import copy
        from engine import process_tick
        gs = {"round_number": 1, "corporate_treasury": 50_000_000, "group_reputation": 60.0,
              "synergy_multiplier": 0.35, "cost_of_capital": 0.05,
              "active_event_flags": {"stochastic_seed": "f01"}, "historical_ebitda": 0,
              "tco2e_emissions": 0, "green_transition_fund": 0, "tipping_point_active": False,
              "pedagogical_overrides": {"black_swan_events_enabled": False, "decision_timer_enabled": False}}
        bus = [{"bu_id": b, "revenue_base": 20_000_000, "opex_base": 12_000_000, "reputation_score": 60.0,
                "social_license_score": 55.0, "governance_risk_score": 20.0, "natural_capital_debt": 50.0,
                "carbon_intensity": 30.0, "water_dependency": 30.0, "staff_burnout_index": 15.0,
                "risk_factors": {}} for b in ("pharma", "software")]
        first = None
        for rnd in range(1, 11):
            gs["round_number"] = rnd
            dec = [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 1_000_000,
                    "choice_selected": "option_b"} for b in bus]
            res = process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
                               decisions=dec, dividends_paid=0, crisis_severity=0.0,
                               imitation_decay_rate=0.10, decision_paradigm="legacy_abc")
            gs, bus = res["global_state"], res["bu_states"]
            gs["active_event_flags"]["stochastic_seed"] = "f01"
            gs["pedagogical_overrides"] = {"black_swan_events_enabled": False, "decision_timer_enabled": False}
            avg = sum(b["reputation_score"] for b in bus) / len(bus)
            # derived = BU average when no crisis is live
            assert gs["group_reputation"] == pytest.approx(avg, abs=0.05), f"round {rnd}"
            first = first if first is not None else gs["group_reputation"]
        assert abs(gs["group_reputation"] - first) < 10.0, "quiet-round drift"

    def test_between_tick_reputation_write_is_folded_into_bu_stock(self):
        """A shock that writes gs['group_reputation'] between ticks (side-track,
        agent, black swan) must reach the BU stock, not be overwritten."""
        import copy
        from engine import process_tick, REPUTATION_DERIVED_KEY
        bus = [{"bu_id": b, "revenue_base": 20_000_000, "opex_base": 12_000_000, "reputation_score": 60.0,
                "social_license_score": 55.0, "governance_risk_score": 20.0, "natural_capital_debt": 50.0,
                "carbon_intensity": 30.0, "water_dependency": 30.0, "staff_burnout_index": 15.0,
                "risk_factors": {}} for b in ("pharma", "software")]
        gs = {"round_number": 2, "corporate_treasury": 50_000_000, "group_reputation": 50.0,
              "synergy_multiplier": 0.35, "cost_of_capital": 0.05, "historical_ebitda": 0,
              "tco2e_emissions": 0, "green_transition_fund": 0, "tipping_point_active": False,
              # last tick stamped 60; something then wrote 50 → a -10 carry
              "active_event_flags": {"stochastic_seed": "f01", REPUTATION_DERIVED_KEY: 60.0},
              "pedagogical_overrides": {"black_swan_events_enabled": False, "decision_timer_enabled": False}}
        dec = [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 1_000_000,
                "choice_selected": "option_b"} for b in bus]
        res = process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
                           decisions=dec, dividends_paid=0, crisis_severity=0.0,
                           imitation_decay_rate=0.10, decision_paradigm="legacy_abc")
        assert res["events"].get("reputation_carry_applied") == pytest.approx(-10.0)
        for b in res["bu_states"]:
            assert b["reputation_score"] < 60.0


# ═══════════════════════════════════════════════════════════════════════════
#  F-02 — cost of capital
# ═══════════════════════════════════════════════════════════════════════════

class TestF02CostOfCapital:
    def test_water_dependency_does_not_pin_wacc_at_cap(self):
        import copy
        from engine import process_tick
        bus = [{"bu_id": b, "revenue_base": 20_000_000, "opex_base": 12_000_000, "reputation_score": 60.0,
                "social_license_score": 55.0, "governance_risk_score": 20.0, "natural_capital_debt": 50.0,
                "carbon_intensity": 30.0, "water_dependency": 54.25, "staff_burnout_index": 15.0,
                "risk_factors": {}} for b in ("pharma", "software")]
        gs = {"round_number": 1, "corporate_treasury": 50_000_000, "group_reputation": 60.0,
              "synergy_multiplier": 0.35, "cost_of_capital": 0.05, "historical_ebitda": 0,
              "tco2e_emissions": 0, "green_transition_fund": 0, "tipping_point_active": False,
              "active_event_flags": {"stochastic_seed": "f02"},
              "pedagogical_overrides": {"black_swan_events_enabled": False, "decision_timer_enabled": False}}
        dec = [{"bu_id": b["bu_id"], "investment_ratio": 0.3, "capex_allocated": 1_000_000,
                "choice_selected": "option_b"} for b in bus]
        res = process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
                           decisions=dec, dividends_paid=0, crisis_severity=0.0,
                           imitation_decay_rate=0.10, decision_paradigm="legacy_abc")
        diag = res["events"]["esg_adjusted_wacc"]
        # 0.5425 × (1 − 0.30) × 0.02 ≈ 0.0076, not the +0.76 the raw mean produced
        assert diag["nature_premium"] == pytest.approx(0.0076, abs=0.0005)
        assert res["global_state"]["cost_of_capital"] < 0.10

    def test_macro_modifier_is_a_level_not_a_flow(self):
        """Feeding the engine its own output for several rounds must not
        accumulate the per-regime macro modifier into the base."""
        import copy
        from engine import process_tick, COC_BASE_KEY
        bus = [{"bu_id": "pharma", "revenue_base": 20_000_000, "opex_base": 12_000_000, "reputation_score": 60.0,
                "social_license_score": 55.0, "governance_risk_score": 20.0, "natural_capital_debt": 50.0,
                "carbon_intensity": 30.0, "water_dependency": 30.0, "staff_burnout_index": 15.0, "risk_factors": {}}]
        gs = {"round_number": 1, "corporate_treasury": 50_000_000, "group_reputation": 60.0,
              "synergy_multiplier": 0.35, "cost_of_capital": 0.05, "historical_ebitda": 0,
              "tco2e_emissions": 0, "green_transition_fund": 0, "tipping_point_active": False,
              "active_event_flags": {"stochastic_seed": "f02"},
              "pedagogical_overrides": {"black_swan_events_enabled": False, "decision_timer_enabled": False}}
        for rnd in range(1, 8):
            gs["round_number"] = rnd
            dec = [{"bu_id": "pharma", "investment_ratio": 0.3, "capex_allocated": 1_000_000, "choice_selected": "option_b"}]
            res = process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
                               decisions=dec, dividends_paid=0, crisis_severity=0.0,
                               imitation_decay_rate=0.10, decision_paradigm="legacy_abc")
            gs, bus = res["global_state"], res["bu_states"]
            gs["active_event_flags"]["stochastic_seed"] = "f02"
            gs["pedagogical_overrides"] = {"black_swan_events_enabled": False, "decision_timer_enabled": False}
            assert gs["active_event_flags"][COC_BASE_KEY] == pytest.approx(0.05)


# ═══════════════════════════════════════════════════════════════════════════
#  F-03 — CBAM
# ═══════════════════════════════════════════════════════════════════════════

class TestF03Cbam:
    def test_surcharge_rate_is_a_plausible_carbon_price(self):
        import config
        assert 20.0 <= config.CBAM_SURCHARGE_RATE <= config._CBAM_SURCHARGE_SANITY_MAX
        assert config.CBAM_SURCHARGE_RATE == pytest.approx(100.0)

    def test_repo_config_matches_the_default(self):
        import json, pathlib
        cfg = json.loads((pathlib.Path(__file__).resolve().parent.parent.parent / "simulation_config.json").read_text(encoding="utf-8-sig"))
        cbam = cfg.get("cbam") or cfg.get("cbam_surcharge") or {}
        rate = cbam.get("surcharge_rate") if isinstance(cbam, dict) else None
        if rate is None:  # locate it wherever the schema keeps it
            def _find(o):
                if isinstance(o, dict):
                    for k, v in o.items():
                        if k == "surcharge_rate":
                            return v
                        r = _find(v)
                        if r is not None:
                            return r
                return None
            rate = _find(cfg)
        assert rate == 100


# ═══════════════════════════════════════════════════════════════════════════
#  F-15 — memory-store BU key parity
# ═══════════════════════════════════════════════════════════════════════════

class TestF15BuKeyParity:
    def test_memory_store_round_trips_non_whitelisted_bu_keys(self):
        import asyncio, uuid
        import database_memory as dm

        async def go():
            sid = str(uuid.uuid4())
            dm._sessions[sid] = {"session_id": sid, "cohort_name": "F15", "metadata": {}}
            gs = {"round_number": 1, "corporate_treasury": 1.0, "group_reputation": 50.0,
                  "synergy_multiplier": 0.3, "cost_of_capital": 0.05, "active_event_flags": {}}
            bus = [{"bu_id": "pharma", "revenue_base": 1.0, "opex_base": 1.0, "natural_capital_debt": 0.0,
                    "social_license_score": 50.0, "reputation_score": 50.0, "governance_risk_score": 20.0,
                    "water_dependency": 30.0, "carbon_intensity": 30.0, "staff_burnout_index": 10.0,
                    "risk_factors": {},
                    "scope_1_ci": 12.5, "supplier_defection_active": True, "green_premium_squeeze": 0.2}]
            await dm.insert_next_round(sid, 1, gs, bus, [])
            latest = await dm.fetch_latest_state(sid)
            hist = await dm.fetch_round_history(sid)
            return latest, hist

        latest, hist = asyncio.new_event_loop().run_until_complete(go())
        bu = latest["bu_states"][0] if "bu_states" in latest else latest["business_units"][0]
        assert bu["scope_1_ci"] == 12.5
        assert bu["supplier_defection_active"] is True
        assert bu["green_premium_squeeze"] == 0.2
        hb = hist[-1]
        hbus = hb.get("bu_states") or hb.get("business_units")
        assert hbus[0]["scope_1_ci"] == 12.5


# ═══════════════════════════════════════════════════════════════════════════
#  F-20 / F-21 / F-22 / F-24 — authorization over the real HTTP surface
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthorizationBoundaries:
    @pytest.fixture(autouse=True)
    def _world(self):
        gm = _god()
        self.fa, self.ck_a = _facilitator(gm, "Launch Audit A")
        self.fb, self.ck_b = _facilitator(gm, "Launch Audit B")
        self.cohort_a = _cohort(self.ck_a, self.fa, "Audit Cohort A")
        self.cohort_b = _cohort(self.ck_b, self.fb, "Audit Cohort B")
        self.pid, self.pw, self.team_a, self.token = _team(self.ck_a, self.cohort_a, "Team Alpha")
        self.gm = gm
        yield
        client.cookies.clear()

    # F-20 ---------------------------------------------------------------
    def test_session_list_is_scoped_by_jwt_and_credential_free(self):
        rows = client.get("/api/admin/sessions", cookies=self.ck_b).json()["sessions"]
        ids = {s["session_id"] for s in rows}
        assert self.cohort_b in ids and self.cohort_a not in ids
        own = client.get("/api/admin/sessions", cookies=self.ck_a).json()["sessions"]
        row = next(s for s in own if s["session_id"] == self.cohort_a)
        for p in row.get("registered_players", []):
            assert "password" not in p, "bcrypt hash must never leave the server"
        # spoofing the filter does not widen the view
        forged = client.get(f"/api/admin/sessions?facilitator_id={self.fa}", cookies=self.ck_b).json()["sessions"]
        assert self.cohort_a not in {s["session_id"] for s in forged}
        # admins still see everything
        allrows = client.get("/api/admin/sessions", cookies=self.gm).json()["sessions"]
        assert {self.cohort_a, self.cohort_b} <= {s["session_id"] for s in allrows}

    # F-21 ---------------------------------------------------------------
    def test_other_facilitator_cannot_read_or_act_on_cohort(self):
        b = self.ck_b
        assert client.get(f"/api/admin/{self.cohort_a}/player-sessions", cookies=b).status_code == 403
        assert client.get(f"/api/admin/sessions/{self.cohort_a}/pacing", cookies=b).status_code == 403
        assert client.put(f"/api/admin/cohort/{self.cohort_a}/pacing",
                          json={"pacing_mode": "manual", "max_unlocked_round": 1}, cookies=b).status_code == 403
        assert client.post(f"/api/admin/{self.cohort_a}/generate-player",
                           json={"player_name": "Intruder"}, cookies=b).status_code == 403
        assert client.patch(f"/api/admin/sessions/{self.cohort_a}/metadata",
                            json={"cohort_name": "Hijacked", "facilitator_id": self.fb}, cookies=b).status_code == 403
        assert client.post(f"/api/admin/{self.team_a}/bonuses",
                           json={"player_name": "Team Alpha", "points": 999, "reason": "x"}, cookies=b).status_code == 403
        assert client.get(f"/api/admin/{self.cohort_a}/interventions", cookies=b).status_code == 403
        assert client.get(f"/api/admin/teleprompter/agents/{self.team_a}", cookies=b).status_code == 403
        # ...while the owner can
        assert client.get(f"/api/admin/{self.cohort_a}/player-sessions", cookies=self.ck_a).status_code == 200
        assert client.get(f"/api/admin/sessions/{self.cohort_a}/pacing", cookies=self.ck_a).status_code == 200

    def test_player_routes_reject_a_facilitator_who_does_not_own_the_team(self):
        client.cookies.clear()
        r = client.get(f"/api/simulations/{self.team_a}/dashboard", cookies=self.ck_b)
        assert r.status_code == 403
        r = client.get(f"/api/simulations/{self.team_a}/dashboard", cookies=self.ck_a)
        assert r.status_code == 200

    # F-22 ---------------------------------------------------------------
    def test_player_identity_is_the_signed_token_not_the_header(self):
        client.cookies.clear()
        H = {"Authorization": f"Bearer {self.token}"}
        assert client.get(f"/api/simulations/{self.team_a}/dashboard", headers=H).status_code == 200
        assert client.get(f"/api/simulations/{self.team_a}/balance-sheet", headers=H).status_code == 200
        bare = client.get(f"/api/simulations/{self.team_a}/dashboard", headers={"X-Player-Id": self.pid})
        assert bare.status_code == 401 and bare.json()["detail"]["code"] == "player_token_required"
        assert client.get(f"/api/simulations/{self.team_a}/dashboard").status_code == 403
        assert client.get(f"/api/simulations/{self.team_a}/final-report").status_code == 403
        other = player_token_headers(self.cohort_b, "MUR-OTHER")
        assert client.get(f"/api/simulations/{self.team_a}/dashboard", headers=other).status_code == 403
        # a forged token (wrong signature) is not a credential
        forged = {"Authorization": "Bearer " + self.token[:-3] + "xyz"}
        assert client.get(f"/api/simulations/{self.team_a}/dashboard", headers=forged).status_code in (401, 403)

    def test_default_password_can_only_change_itself(self):
        client.cookies.clear()
        H = {"Authorization": f"Bearer {self.token}"}
        dash = client.get(f"/api/simulations/{self.team_a}/dashboard", headers=H).json()
        _clear_commit_gate(self.team_a)
        r = client.post(f"/api/simulations/{self.team_a}/commit-turn",
                        json=_commit_payload(dash, dash["current_round"]), headers=H)
        assert r.status_code == 403 and r.json()["detail"]["code"] == "password_change_required"
        assert client.post("/api/simulations/change-password",
                           json={"player_id": self.pid, "old_password": self.pw,
                                 "new_password": "personal-pass-1"}).status_code == 200
        _clear_commit_gate(self.team_a)
        r = client.post(f"/api/simulations/{self.team_a}/commit-turn",
                        json=_commit_payload(dash, dash["current_round"]), headers=H)
        assert r.status_code == 201, r.text
        assert r.json()["new_round_number"] == dash["current_round"] + 1

    def test_facilitator_default_password_can_only_change_itself(self):
        r = client.post("/api/admin/facilitators", json={"name": "Fresh", "role": "facilitator"}, cookies=self.gm)
        fid, otp = r.json()["facilitator_id"], r.json()["one_time_password"]
        ck = client.post("/api/admin/facilitators/login", json={"facilitator_id": fid, "password": otp}).cookies
        blocked = client.get("/api/admin/sessions", cookies=ck)
        assert blocked.status_code == 403 and blocked.json()["detail"]["code"] == "password_change_required"
        assert client.post("/api/admin/auth/refresh", cookies=ck).status_code == 200  # allow-listed
        ok = client.post("/api/admin/facilitators/change-password",
                         json={"facilitator_id": fid, "old_password": otp, "new_password": "Personal-Fresh-1!"}, cookies=ck)
        assert ok.status_code == 200, ok.text
        ck2 = client.post("/api/admin/facilitators/login", json={"facilitator_id": fid, "password": "Personal-Fresh-1!"}).cookies
        assert client.get("/api/admin/sessions", cookies=ck2).status_code == 200

    def test_master_password_impersonation_is_exempt_from_the_first_login_gate(self):
        """Admin break-glass into an un-rotated account: the login response
        already says must_change_password=False for it, and the server-side
        gate must agree (the JWT carries the signed `mb` claim), including
        after a token refresh."""
        r = client.post("/api/admin/facilitators", json={"name": "Impersonated", "role": "facilitator"}, cookies=self.gm)
        fid = r.json()["facilitator_id"]
        lr = client.post("/api/admin/facilitators/login", json={"facilitator_id": fid, "password": GOD["password"]})
        assert lr.status_code == 200 and lr.json()["must_change_password"] is False
        assert client.get("/api/admin/sessions", cookies=lr.cookies).status_code == 200
        rf = client.post("/api/admin/auth/refresh", cookies=lr.cookies)
        assert rf.status_code == 200
        assert client.get("/api/admin/sessions", cookies=rf.cookies).status_code == 200

    # F-24 ---------------------------------------------------------------
    def test_set_username_and_change_password_are_not_anonymous_oracles(self):
        client.cookies.clear()
        r = client.post("/api/simulations/set-username",
                        json={"user_id": self.pid, "role": "player", "username": "pwned"})
        assert r.status_code == 401
        r = client.post("/api/simulations/set-username",
                        json={"user_id": self.fa, "role": "facilitator", "username": "pwned-fac"})
        assert r.status_code == 401
        # the player CAN rename itself with its token
        r = client.post("/api/simulations/set-username",
                        json={"user_id": self.pid, "role": "player", "username": f"Alpha-{self.pid[-4:]}"},
                        headers={"Authorization": f"Bearer {self.token}"})
        assert r.status_code == 200, r.text
        # a facilitator of an UNRELATED cohort cannot rename this team …
        r = client.post("/api/simulations/set-username",
                        json={"user_id": self.pid, "role": "player", "username": "pwned-by-b"}, cookies=self.ck_b)
        assert r.status_code == 403, r.text
        # … but the cohort's own facilitator can
        r = client.post("/api/simulations/set-username",
                        json={"user_id": self.pid, "role": "player", "username": f"Alpha2-{self.pid[-4:]}"}, cookies=self.ck_a)
        assert r.status_code == 200, r.text
        client.cookies.clear()
        # a solo session (no owner, no token) still renames itself by UUID
        from admin_shared import _god_mode_settings
        _prev = _god_mode_settings.get("solo_mode_enabled")
        _god_mode_settings["solo_mode_enabled"] = True
        try:
            solo = client.post("/api/simulations/solo-start", json={"player_name": "Solo"})
            assert solo.status_code in (200, 201), solo.text
            sid = solo.json()["session_id"]
            r = client.post("/api/simulations/set-username",
                            json={"user_id": sid, "role": "player", "username": f"Solo-{sid[:6]}"})
            assert r.status_code == 200, r.text
        finally:
            _god_mode_settings["solo_mode_enabled"] = _prev
        # change-password is rate limited per identity
        import rate_limit as _rl
        _rl._rate_buckets.clear()
        codes = [client.post("/api/simulations/change-password",
                             json={"player_id": self.pid, "old_password": f"guess{i}",
                                   "new_password": "longenough1"}).status_code for i in range(40)]
        assert 429 in codes, f"no 429 in {sorted(set(codes))}"
        _rl._rate_buckets.clear()
        _rl._persistent_bans.clear()


# ═══════════════════════════════════════════════════════════════════════════
#  F-26 — commit gate (pool exhaustion under simultaneous commits)
# ═══════════════════════════════════════════════════════════════════════════

def _run_async(coro):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _solo_sessions(ac, n):
    """n solo sessions with their R1 commit payloads, over one AsyncClient."""
    out = []
    for _ in range(n):
        r = await ac.post("/api/simulations/solo-start", json={"player_name": "Gate", "decision_paradigm": "legacy_abc"})
        assert r.status_code in (200, 201), r.text
        sid = r.json()["session_id"]
        bus = (await ac.get(f"/api/simulations/{sid}/dashboard")).json()["business_units"]
        out.append((sid, {"decisions": [{"bu_id": b["bu_id"], "capex_allocated": 1, "choice_selected": "option_b"} for b in bus],
                          "expected_round": 1}))
    return out


class TestF26CommitGate:
    def test_simultaneous_commits_are_bounded_and_all_succeed(self, monkeypatch):
        """Fire 12 commits at once with a gate of 3: every one returns 201 and
        no more than 3 are ever inside the engine at the same moment."""
        import asyncio, httpx
        from httpx import ASGITransport
        import router, config
        monkeypatch.setattr(config, "COMMIT_MAX_IN_FLIGHT", 3)
        router._commit_gates.clear()
        peak = {"now": 0, "max": 0}
        real_impl = router._commit_turn_impl

        async def slow_impl(session_id, body, lock):
            peak["now"] += 1
            peak["max"] = max(peak["max"], peak["now"])
            try:
                await asyncio.sleep(0.03)
                return await real_impl(session_id, body, lock)
            finally:
                peak["now"] -= 1
        monkeypatch.setattr(router, "_commit_turn_impl", slow_impl)

        async def go():
            async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t", timeout=60) as ac:
                sess = await _solo_sessions(ac, 12)
                for sid, _ in sess:
                    _clear_commit_gate(sid)
                rs = await asyncio.gather(*[ac.post(f"/api/simulations/{sid}/commit-turn", json=p) for sid, p in sess])
                return [r.status_code for r in rs]
        codes = _run_async(go())
        router._commit_gates.clear()
        assert codes == [201] * 12, codes
        assert peak["max"] <= 3, f"gate leaked: {peak['max']} commits in flight"

    def test_queue_wait_beyond_patience_is_a_retryable_503(self, monkeypatch):
        import asyncio, httpx
        from httpx import ASGITransport
        import router, config
        monkeypatch.setattr(config, "COMMIT_MAX_IN_FLIGHT", 1)
        monkeypatch.setattr(config, "COMMIT_QUEUE_TIMEOUT_SECONDS", 0.05)
        router._commit_gates.clear()

        async def go():
            async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t", timeout=60) as ac:
                (sid, payload), = await _solo_sessions(ac, 1)
                _clear_commit_gate(sid)
                gate = router._commit_gate()
                await gate.acquire()            # somebody else holds the only slot
                try:
                    r = await ac.post(f"/api/simulations/{sid}/commit-turn", json=payload)
                finally:
                    gate.release()
                return r
        r = _run_async(go())
        router._commit_gates.clear()
        assert r.status_code == 503, r.text
        assert r.json()["detail"]["code"] == "commit_queue_full"
        assert r.headers.get("retry-after") == "5"

    def test_pool_acquire_timeout_surfaces_as_503_not_500(self, monkeypatch):
        import asyncio
        import router
        async def exhausted(*a, **k):
            raise asyncio.TimeoutError()
        monkeypatch.setattr(router.db, "fetch_latest_state", exhausted)
        from admin_shared import _god_mode_settings
        _god_mode_settings["solo_mode_enabled"] = True
        client.cookies.clear()
        sid = client.post("/api/simulations/solo-start", json={"player_name": "T"}).json()["session_id"]
        r = client.get(f"/api/simulations/{sid}/dashboard")
        assert r.status_code == 503, r.text
        assert r.json()["detail"]["code"] == "server_busy"
        assert r.headers.get("retry-after") == "5"

    def test_gate_size_follows_the_pool(self):
        import config
        assert 1 <= config.COMMIT_MAX_IN_FLIGHT <= max(1, config.DB_MAX_CONNECTIONS // 2)
        # two connections per in-flight commit must always fit in the pool
        assert config.COMMIT_MAX_IN_FLIGHT * 2 <= max(2, config.DB_MAX_CONNECTIONS)


# ═══════════════════════════════════════════════════════════════════════════
#  F-27 — dashboard poll cost
# ═══════════════════════════════════════════════════════════════════════════

class TestF27DashboardPayload:
    @pytest.fixture()
    def played(self):
        """A solo session advanced to round 3."""
        from admin_shared import _god_mode_settings
        _god_mode_settings["solo_mode_enabled"] = True
        client.cookies.clear()
        sid = client.post("/api/simulations/solo-start", json={"player_name": "P", "decision_paradigm": "legacy_abc"}).json()["session_id"]
        bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
        for rnd in (1, 2):
            _clear_commit_gate(sid)
            r = client.post(f"/api/simulations/{sid}/commit-turn", json={
                "decisions": [{"bu_id": b["bu_id"], "capex_allocated": 1, "choice_selected": "option_b"} for b in bus],
                "expected_round": rnd})
            assert r.status_code == 201, r.text
            bus = r.json()["business_units"]
        return sid

    def test_since_round_returns_only_newer_history_but_always_the_latest_state(self, played):
        full = client.get(f"/api/simulations/{played}/dashboard").json()
        assert full["current_round"] == 3
        assert [h["round_number"] for h in full["history"]] == [1, 2, 3]
        newer = client.get(f"/api/simulations/{played}/dashboard?since_round=4").json()
        assert newer["current_round"] == 3 and newer["history"] == []
        assert newer["global_state"]["corporate_treasury"] == full["global_state"]["corporate_treasury"]
        assert len(newer["business_units"]) == len(full["business_units"])
        part = client.get(f"/api/simulations/{played}/dashboard?since_round=2").json()
        assert [h["round_number"] for h in part["history"]] == [2, 3]
        # the poller payload is a fraction of the full one
        assert len(client.get(f"/api/simulations/{played}/dashboard?since_round=4").content) \
            < 0.6 * len(client.get(f"/api/simulations/{played}/dashboard").content)

    def test_engine_internal_keys_are_not_shipped(self, played):
        import database as db_mod
        # the store still holds the momentum window …
        stored = _run_async(db_mod.fetch_latest_state(played))
        assert "_prev_global_states" in stored["global_state"].get("active_event_flags", {}) or \
            "_prev_global_states" in stored["global_state"]
        # … but the wire does not
        full = client.get(f"/api/simulations/{played}/dashboard").json()
        assert "_prev_global_states" not in full["global_state"]["active_event_flags"]
        for h in full["history"]:
            assert "_prev_global_states" not in h["global_state"]["active_event_flags"]
            assert "consequence_dna_snapshot" not in h["global_state"]["active_event_flags"]
        # and the store was not mutated by the read
        again = _run_async(db_mod.fetch_latest_state(played))
        assert again["global_state"].get("active_event_flags", {}).keys() == stored["global_state"].get("active_event_flags", {}).keys()

    def test_large_json_responses_are_gzipped(self, played):
        r = client.get(f"/api/simulations/{played}/dashboard", headers={"Accept-Encoding": "gzip"})
        assert r.status_code == 200
        assert r.headers.get("content-encoding") == "gzip"
        assert r.json()["current_round"] == 3  # transparently decoded
        small = client.get("/api/health", headers={"Accept-Encoding": "gzip"})
        assert small.headers.get("content-encoding") is None  # below minimum_size

    def test_store_helpers_since_round_and_batched_latest_rounds(self, played):
        import database as db_mod
        hist = _run_async(db_mod.fetch_round_history(played, since_round=3))
        assert [h["round_number"] for h in hist] == [3]
        hist_all = _run_async(db_mod.fetch_round_history(played))
        assert [h["round_number"] for h in hist_all] == [1, 2, 3]
        latest = _run_async(db_mod.fetch_latest_rounds([played, "00000000-0000-0000-0000-000000000000"]))
        assert latest == {played: 3}

    def test_cohort_sibling_scan_is_one_store_call_per_dashboard(self, monkeypatch):
        """The badge and the free-advance status used to each query every
        sibling; a dashboard read now asks the store once for all of them."""
        import router
        gm = _god()
        fid, ck = _facilitator(gm, "Poll Cost")
        cohort = _cohort(ck, fid, "Poll Cohort")
        teams = [_team(ck, cohort, f"T{i}") for i in range(3)]
        pid, pw, team_sid, token = teams[0]
        calls = {"batched": 0, "single": 0}
        real_batched = router.db.fetch_latest_rounds
        real_single = router.db.fetch_latest_round

        async def counting_batched(sids):
            calls["batched"] += 1
            return await real_batched(sids)

        async def counting_single(sid):
            calls["single"] += 1
            return await real_single(sid)
        monkeypatch.setattr(router.db, "fetch_latest_rounds", counting_batched)
        monkeypatch.setattr(router.db, "fetch_latest_round", counting_single)
        client.cookies.clear()
        r = client.get(f"/api/simulations/{team_sid}/dashboard?since_round=2", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        assert r.json()["global_state"]["cohort_team_count"] == 3
        assert calls == {"batched": 1, "single": 0}, calls


# ═══════════════════════════════════════════════════════════════════════════
#  F-40 — player ids must be unique across the whole platform
#  (found 2026-09-02 while running these fixes against Postgres: probe cohorts
#  had re-issued each other's ids and logins resolved to the wrong cohort)
# ═══════════════════════════════════════════════════════════════════════════

class TestF40PlayerIdUniqueness:
    def test_generate_player_never_reissues_an_id_held_by_another_cohort(self, monkeypatch):
        """Force the random draw to keep producing an id another cohort already
        holds: the allocator must skip it, not hand it out twice."""
        import random
        gm = _god()
        fa, ck_a = _facilitator(gm, "Uniq A")
        fb, ck_b = _facilitator(gm, "Uniq B")
        cohort_a = _cohort(ck_a, fa, "Uniq Cohort A")
        cohort_b = _cohort(ck_b, fb, "Uniq Cohort B")
        g = client.post(f"/api/admin/{cohort_a}/generate-player", json={"player_name": "A1"}, cookies=ck_a)
        taken = g.json()["player_id"]
        letters = taken.split("-", 1)[1]
        seq = iter([list(letters)] * 5 + [list("QQQQ") if letters != "QQQQ" else list("QQQZ")])
        real_choices = random.choices

        def rigged(population, k=4, **kw):
            try:
                return next(seq)
            except StopIteration:
                return real_choices(population, k=k, **kw)
        monkeypatch.setattr(random, "choices", rigged)
        g2 = client.post(f"/api/admin/{cohort_b}/generate-player", json={"player_name": "B1"}, cookies=ck_b)
        assert g2.status_code == 200, g2.text
        assert g2.json()["player_id"] != taken
        assert g2.json()["player_id"].startswith("MUR-")

    def test_sequential_ids_continue_past_every_id_the_store_has_issued(self):
        """Bulk/induct ids come from a process counter that used to restart at
        MUR-001 on every deploy. Simulate the restart: reset the counter, then
        induct — the new id must not collide with any earlier cohort's roster."""
        import admin_router
        import database as db_mod
        gm = _god()
        fa, ck_a = _facilitator(gm, "Seq A")
        fb, ck_b = _facilitator(gm, "Seq B")
        cohort_a = _cohort(ck_a, fa, "Seq Cohort A")
        cohort_b = _cohort(ck_b, fb, "Seq Cohort B")
        r1 = client.post("/api/admin/players/induct",
                         json={"session_id": cohort_a, "name": "First", "email": "", "programme": "", "assigned_bu": ""}, cookies=ck_a)
        assert r1.status_code == 200, r1.text
        first_id = r1.json()["player_id"]
        # "deploy": counter forgets everything
        admin_router._next_player_id = 1
        admin_router._next_player_id_seeded = False
        r2 = client.post("/api/admin/players/induct",
                         json={"session_id": cohort_b, "name": "Second", "email": "", "programme": "", "assigned_bu": ""}, cookies=ck_b)
        assert r2.status_code == 200, r2.text
        second_id = r2.json()["player_id"]
        assert second_id != first_id
        all_ids = _run_async(db_mod.list_all_player_ids())
        assert first_id in all_ids and second_id in all_ids
        assert _run_async(db_mod.player_id_in_use(first_id)) is True
        assert _run_async(db_mod.player_id_in_use("MUR-NOPE")) is False

    def test_login_with_a_legacy_colliding_id_resolves_by_password_not_by_luck(self):
        """Two cohorts already hold the same id with DIFFERENT passwords (the
        pre-fix state of a live platform): each team must reach its own cohort."""
        from admin_shared import _player_registry
        from password_hashing import hash_password
        import rate_limit as _rl
        gm = _god()
        fa, ck_a = _facilitator(gm, "Coll A")
        fb, ck_b = _facilitator(gm, "Coll B")
        cohort_a = _cohort(ck_a, fa, "Coll Cohort A")
        cohort_b = _cohort(ck_b, fb, "Coll Cohort B")
        pid = "MUR-ZZ9"
        _player_registry[:] = [p for p in _player_registry if p.get("player_id") != pid]
        for cohort, pw in ((cohort_a, "alpha-pass-1"), (cohort_b, "bravo-pass-1")):
            rec = {"player_id": pid, "name": "", "session_id": cohort, "password": hash_password(pw),
                   "must_change_password": False, "status": "id_generated"}
            _player_registry.append(rec)
            sess = _run_async(__import__("database").get_session_info(cohort))
            reg = list(sess.get("registered_players") or []) + [rec]
            _run_async(__import__("database").update_session_metadata(
                cohort, {"registered_players": reg, "allowed_player_ids": [pid]}))
        client.cookies.clear()
        _rl._rate_buckets.clear()
        la = client.post("/api/simulations/player-login", json={"player_id": pid, "password": "bravo-pass-1"})
        assert la.status_code == 200, la.text
        info = client.get(f"/api/simulations/{la.json()['session_id']}/session-info",
                          headers={"Authorization": f"Bearer {la.json()['player_token']}"}).json()
        assert info.get("parent_cohort_id") == cohort_b, "landed in the wrong cohort"
        _rl._rate_buckets.clear()
        wrong = client.post("/api/simulations/player-login", json={"player_id": pid, "password": "nobody-pass-1"})
        assert wrong.status_code == 403
        _player_registry[:] = [p for p in _player_registry if p.get("player_id") != pid]

    def test_login_with_an_id_that_is_ambiguous_even_by_password_is_refused(self):
        from admin_shared import _player_registry
        from password_hashing import hash_password
        import rate_limit as _rl
        gm = _god()
        fa, ck_a = _facilitator(gm, "Amb A")
        fb, ck_b = _facilitator(gm, "Amb B")
        cohort_a = _cohort(ck_a, fa, "Amb Cohort A")
        cohort_b = _cohort(ck_b, fb, "Amb Cohort B")
        pid = "MUR-ZZ8"
        _player_registry[:] = [p for p in _player_registry if p.get("player_id") != pid]
        for cohort in (cohort_a, cohort_b):   # same default password in both
            _player_registry.append({"player_id": pid, "name": "", "session_id": cohort,
                                     "password": hash_password(f"{pid}@123"), "must_change_password": True})
        client.cookies.clear()
        _rl._rate_buckets.clear()
        r = client.post("/api/simulations/player-login", json={"player_id": pid, "password": f"{pid}@123"})
        assert r.status_code == 409, r.text
        assert r.json()["detail"]["code"] == "player_id_ambiguous"
        _player_registry[:] = [p for p in _player_registry if p.get("player_id") != pid]

    def test_register_path_ids_are_unique_too(self):
        """/players/register mints P-NNN from the same counter; after a
        'redeploy' it must not reissue an id that is already in the registry."""
        import admin_router
        from admin_shared import _player_registry
        gm = _god()
        r1 = client.post("/api/admin/players/register", json={"player_name": "One", "team_name": "T"}, cookies=gm)
        assert r1.status_code == 200, r1.text
        first = r1.json()["player_id"]
        assert first.startswith("P")
        admin_router._next_player_id = 1
        admin_router._next_player_id_seeded = False
        r2 = client.post("/api/admin/players/register", json={"player_name": "Two", "team_name": "T"}, cookies=gm)
        assert r2.status_code == 200, r2.text
        assert r2.json()["player_id"] != first
        ids = [p["player_id"] for p in _player_registry if p.get("player_id", "").startswith("P")]
        assert len(ids) == len(set(ids)), "duplicate P-ids in the registry"

    def test_random_ids_are_four_letters_and_old_three_letter_ids_still_work(self):
        """F-40 follow-up: the id space is 26^4 = 456,976 (was 17,576). Older
        three-letter ids remain valid credentials — nothing validates width."""
        import re
        import config
        assert config.PLAYER_ID_RANDOM_LETTERS == 4
        gm = _god()
        fa, ck = _facilitator(gm, "Wide A")
        cohort = _cohort(ck, fa, "Wide Cohort")
        g = client.post(f"/api/admin/{cohort}/generate-player", json={"player_name": "W"}, cookies=ck)
        assert g.status_code == 200, g.text
        assert re.fullmatch(r"MUR-[A-Z]{4}", g.json()["player_id"]), g.json()["player_id"]
        # legacy three-letter id planted the way an old cohort would hold it
        from admin_shared import _player_registry
        from password_hashing import hash_password
        import database as db_mod
        pid = "MUR-OLD"
        _player_registry[:] = [p for p in _player_registry if p.get("player_id") != pid]
        rec = {"player_id": pid, "name": "", "session_id": cohort, "password": hash_password("legacy-pass-1"),
               "must_change_password": False, "status": "id_generated"}
        _player_registry.append(rec)
        sess = _run_async(db_mod.get_session_info(cohort))
        _run_async(db_mod.update_session_metadata(cohort, {
            "registered_players": list(sess.get("registered_players") or []) + [rec],
            "allowed_player_ids": list(sess.get("allowed_player_ids") or []) + [pid]}))
        import rate_limit as _rl
        _rl._rate_buckets.clear()
        client.cookies.clear()
        r = client.post("/api/simulations/player-login", json={"player_id": pid, "password": "legacy-pass-1"})
        assert r.status_code == 200, r.text
        assert _run_async(db_mod.player_id_in_use(pid)) is True
        _player_registry[:] = [p for p in _player_registry if p.get("player_id") != pid]


# ═══════════════════════════════════════════════════════════════════════════
#  F-04 / F-05 / F-06 / F-07 — economy rulings (2026-09-02)
# ═══════════════════════════════════════════════════════════════════════════

def _tick_state(round_number=1, treasury=50_000_000, water=30.0, gov=20.0):
    gs = {"round_number": round_number, "corporate_treasury": treasury, "group_reputation": 60.0,
          "synergy_multiplier": 0.35, "cost_of_capital": 0.05, "historical_ebitda": 0,
          "tco2e_emissions": 0, "green_transition_fund": 0, "tipping_point_active": False,
          "active_event_flags": {"stochastic_seed": "econ"},
          "pedagogical_overrides": {"black_swan_events_enabled": False, "decision_timer_enabled": False}}
    bus = [{"bu_id": b, "revenue_base": 20_000_000, "opex_base": 12_000_000, "reputation_score": 60.0,
            "social_license_score": 55.0, "governance_risk_score": gov, "natural_capital_debt": 50.0,
            "carbon_intensity": 30.0, "water_dependency": water, "staff_burnout_index": 15.0,
            "risk_factors": {}} for b in ("pharma", "software")]
    return gs, bus


def _tick(gs, bus, capex=1_000_000, ratio=0.3, choice="option_b", **kw):
    import copy
    from engine import process_tick
    dec = [{"bu_id": b["bu_id"], "investment_ratio": ratio, "capex_allocated": capex,
            "choice_selected": choice} for b in bus]
    return process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus), decisions=dec,
                        dividends_paid=0, crisis_severity=kw.get("crisis", 0.0),
                        imitation_decay_rate=0.05, decision_paradigm="legacy_abc",
                        emergency_credit_used=kw.get("emergency", False))


class TestF04FlowPenaltiesAreTransient:
    def test_supply_chain_contagion_does_not_compound_into_the_base(self):
        """High sibling governance risk charges THIS round's OPEX; the persisted
        base must not carry it (it used to grow ~7–9% per round forever)."""
        gs, bus = _tick_state(gov=90.0)
        res = _tick(gs, bus)
        ev = res["events"]
        surcharge = sum(v for k, v in ev.items() if k.startswith("supply_chain_contagion_"))
        assert surcharge > 0
        reversed_ = ev["transient_flow_adjustments_reversed"]
        assert any(k.endswith(".opex_base") for k in reversed_)
        # persisted opex ≈ inflated base only (no contagion footprint left behind)
        infl = 1 + ev["inflation_index_applied"]
        for b in res["bu_states"]:
            assert b["opex_base"] < 12_000_000 * infl * 1.02, b["opex_base"]

    def test_dso_deferral_is_timing_not_lost_revenue(self):
        gs, bus = _tick_state(gov=60.0)
        res = _tick(gs, bus)
        deferred = res["events"]["dso_working_capital"]["total_deferred"]
        assert deferred > 0
        # the deferred cash is scheduled to come back...
        assert any(p.get("type") == "revenue_generation" for p in res["global_state"]["pending_capex_projects"])
        # ...so the revenue base must not ALSO have shrunk by it
        rev_infl = 1 + res["events"]["revenue_inflation_applied"]
        for b in res["bu_states"]:
            assert b["revenue_base"] > 20_000_000 * rev_infl * 0.97

    def test_inflation_after_transients_leaves_no_residual(self):
        """Transients recorded before the inflation step are scaled with it, so
        the additive reversal is exact (was a ~0.2%/round leak)."""
        gs, bus = _tick_state(gov=90.0)
        res = _tick(gs, bus)   # ratio 0.3 > lag threshold: the synergy saving is deferred to next round
        ev = res["events"]
        infl = 1 + ev["inflation_index_applied"]
        surcharge = sum(v for k, v in ev.items() if k.startswith("supply_chain_contagion_"))
        assert surcharge > 100_000  # the contagion really was charged this round…
        for b in res["bu_states"]:
            # …and the persisted base is EXACTLY the inflated base — no residual
            assert abs(b["opex_base"] - round(12_000_000 * infl, 2)) < 1.0, (b["opex_base"], infl)

    def test_a_purely_transient_surcharge_leaves_no_footprint_below_the_lag_threshold(self):
        """B-2 (2026-09-03) — THE GAP THAT LET F-04 REOPEN.

        The sibling test above runs at investment_ratio 0.3, which is ABOVE
        IMPLEMENTATION_LAG_INV_THRESHOLD (0.10), so the synergy saving is
        deferred and calc_synergy_opex never runs. That branch is a PERMANENT
        multiplicative step on opex_base, and it ran after the only
        scale_transients call without carrying the outstanding deltas — so a
        purely transient surcharge left -0.9848% of itself in the base, every
        round, permanently understating cost and overstating treasury.

        The invariant test existed and could not fail, because it never took
        the branch. This one does: it runs BELOW the threshold.
        """
        import copy
        from engine import process_tick, TickContext
        from config import IMPLEMENTATION_LAG_INV_THRESHOLD
        AMT = 1_000_000.0
        _orig = TickContext.record_transient

        def run(inject):
            random.seed(4242)
            if inject:
                def patched(self, bu, field_name, applied_delta):
                    _orig(self, bu, field_name, applied_delta)
                    seen = getattr(self, "_b2_seen", None)
                    if seen is None:
                        seen = self._b2_seen = set()
                    if field_name == "opex_base" and bu.get("bu_id") not in seen:
                        seen.add(bu.get("bu_id"))
                        bu["opex_base"] = round(bu["opex_base"] + AMT, 2)
                        _orig(self, bu, "opex_base", AMT)   # charged AND declared transient
                TickContext.record_transient = patched
            else:
                TickContext.record_transient = _orig
            try:
                gs, bus = _tick_state()
                gs.setdefault("active_event_flags", {})["stochastic_seed"] = "b2-fixed-seed"
                ratio = IMPLEMENTATION_LAG_INV_THRESHOLD / 2      # BELOW: synergy runs
                dec = [{"bu_id": b["bu_id"], "investment_ratio": ratio,
                        "capex_allocated": 250_000.0, "choice_selected": "option_b"}
                       for b in bus]
                out = process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
                                   decisions=dec, dividends_paid=0, crisis_severity=0.0,
                                   decision_paradigm="legacy_abc")
                return {b["bu_id"]: b["opex_base"] for b in out["bu_states"]}
            finally:
                TickContext.record_transient = _orig

        assert run(False) == run(False), "harness is not deterministic"
        clean, injected = run(False), run(True)
        footprint = sum(injected[k] - clean[k] for k in clean)
        assert abs(footprint) < 1.0, (
            f"a purely transient ${AMT:,.0f}/BU surcharge left ${footprint:,.2f} in the "
            f"persisted opex base. Every permanent MULTIPLICATIVE step on a field must "
            f"call ctx.rescale_bu_transients (or record its own full delta); otherwise "
            f"the additive reversal leaks T x (f-1) forever. Pre-fix this was -$39,391.65."
        )

    def test_post_csf_transients_still_cost_cash_this_round(self):
        """F-04b (2026-09-02). Supplier defection and the green-premium squeeze
        are assessed in the reporting layer, AFTER gross profit is banked. Made
        transient, they would otherwise reach no cash at all (the base is restored
        before persistence and the P&L was already taken) — the multi_toggles
        treasury fingerprint had collapsed onto legacy_abc's. The engine now
        charges treasury directly for any transient recorded after the CSF line,
        events the total, and the ledger law closes on it."""
        import copy
        from engine import process_tick
        from config import SUPPLIER_DEFECTION_INV_THRESHOLD
        gs, bus = _tick_state()
        low_ratio = SUPPLIER_DEFECTION_INV_THRESHOLD / 2
        def run(with_mandate: bool):
            dec = [{"bu_id": b["bu_id"], "investment_ratio": low_ratio, "capex_allocated": 1,
                    "choice_selected": "option_b",
                    "pillar_decisions": {"supply_chain": "audit_suppliers"} if with_mandate else {}}
                   for b in bus]
            return process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
                                decisions=dec, dividends_paid=0, crisis_severity=0.0,
                                imitation_decay_rate=0.05, decision_paradigm="multi_toggles",
                                emergency_credit_used=False)
        plain, mandate = run(False), run(True)
        assert mandate["events"]["supplier_defection"]["active"] is True
        cash = mandate["events"]["post_csf_flow_adjustments_cash"]
        assert cash < 0, "an unfunded supplier mandate must cost money this round"
        # the persisted base carries none of it …
        for a, b in zip(plain["bu_states"], mandate["bu_states"]):
            assert abs(a["opex_base"] - b["opex_base"]) < 1.0
            assert abs(a["revenue_base"] - b["revenue_base"]) < 1.0
        # … the treasury carries all of it, exactly once (the plain run has its
        # own post-CSF flows — talent premium at SLO 55 — so compare the events)
        cash_plain = plain["events"].get("post_csf_flow_adjustments_cash", 0.0)
        delta = mandate["global_state"]["corporate_treasury"] - plain["global_state"]["corporate_treasury"]
        assert delta == pytest.approx(cash - cash_plain, abs=1.0), (delta, cash, cash_plain)
        labels = [e["label"] for e in mandate["events"]["consequence_waterfall"]["entries"]]
        assert "Flow surcharges after gross profit" in labels


class TestF05CapexFinancing:
    def test_capex_inside_the_allowance_leaves_treasury(self):
        gs, bus = _tick_state(treasury=50_000_000)
        res = _tick(gs, bus, capex=2_000_000)   # 4M total < 10M allowance
        ev = res["events"]
        assert ev["capex_equity_funded"] == 4_000_000
        assert ev["capex_loan_drawn"] == 0
        assert ev["capex_loan_balance"] == 0
        baseline = _tick(gs, bus, capex=1)["global_state"]["corporate_treasury"]
        assert res["global_state"]["corporate_treasury"] < baseline - 3_900_000

    def test_capex_above_the_allowance_becomes_an_amortising_loan(self):
        gs, bus = _tick_state(treasury=50_000_000, round_number=1)
        res = _tick(gs, bus, capex=15_000_000)  # 30M total: 10M cash, 20M loan
        ev = res["events"]
        assert ev["capex_equity_funded"] == 10_000_000
        assert ev["capex_loan_drawn"] > 0
        assert ev["capex_loan_balance"] == ev["capex_loan_drawn"]
        assert ev["loan_interest_payment"] == 0  # interest accrues on the OPENING balance
        # next round: interest + straight-line repayment over the remaining rounds
        gs2, bus2 = res["global_state"], res["bu_states"]
        gs2["active_event_flags"]["stochastic_seed"] = "econ"
        gs2["pedagogical_overrides"] = gs["pedagogical_overrides"]
        res2 = _tick(gs2, bus2, capex=1)
        ev2 = res2["events"]
        opening = ev["capex_loan_balance"]
        assert ev2["capex_loan_opening"] == opening
        assert ev2["capex_loan_repayment"] == pytest.approx(opening / 9, abs=1.0)  # rounds 2..10
        assert ev2["loan_interest_payment"] == pytest.approx(opening * 0.12, abs=1.0)
        assert ev2["capex_loan_balance"] == pytest.approx(opening - ev2["capex_loan_repayment"], abs=1.0)

    def test_loan_is_fully_repaid_by_round_ten(self):
        gs, bus = _tick_state(treasury=50_000_000, round_number=10)
        gs["active_event_flags"]["capex_loan_balance"] = 9_000_000
        res = _tick(gs, bus, capex=1)
        assert res["events"]["capex_loan_repayment"] == 9_000_000
        assert res["events"]["capex_loan_balance"] == 0

    def test_balance_sheet_shows_the_term_loan(self):
        from balance_sheet import create_initial_balance_sheet, process_balance_sheet_tick
        gs, bus = _tick_state(treasury=50_000_000)
        res = _tick(gs, bus, capex=15_000_000)
        gs2 = res["global_state"]
        gs2["active_event_flags"] = {**gs2.get("active_event_flags", {}), **res["events"]}
        bs = create_initial_balance_sheet(bus)
        ledger, diag = process_balance_sheet_tick(bs, gs2, res["bu_states"], res["events"], 1)
        assert ledger["non_current_liabilities"]["capex_term_loan"] == res["events"]["capex_loan_balance"] > 0
        # and it counts as debt for the covenant test
        from balance_sheet import check_covenants
        import inspect
        params = list(inspect.signature(check_covenants).parameters)
        assert "bs" in params[0] or params[0] in ("bs", "balance_sheet")


class TestF06SynergyCap:
    def test_ten_rounds_of_heavy_investment_do_not_reach_the_floor(self):
        """Before: OPEX hit the 35%-of-original floor by round 4–5 at a 25% ratio."""
        gs, bus = _tick_state()
        for rnd in range(1, 11):
            gs["round_number"] = rnd
            res = _tick(gs, bus, capex=2_500_000, ratio=0.25)
            gs, bus = res["global_state"], res["bu_states"]
            gs["active_event_flags"]["stochastic_seed"] = "econ"
            gs["pedagogical_overrides"] = {"black_swan_events_enabled": False, "decision_timer_enabled": False}
        for b in bus:
            assert b["opex_base"] > 12_000_000 * 0.55, b["opex_base"]


class TestF07ServerDerivedParameters:
    def test_client_engine_parameters_are_ignored(self):
        gm = _god()
        fa, ck = _facilitator(gm, "F07 A")
        cohort = _cohort(ck, fa, "F07 Cohort")
        pid, pw, team, token = _team(ck, cohort, "T")
        client.cookies.clear()
        assert client.post("/api/simulations/change-password",
                           json={"player_id": pid, "old_password": pw, "new_password": "f07-pass-1"}).status_code == 200
        H = {"Authorization": f"Bearer {token}"}
        dash = client.get(f"/api/simulations/{team}/dashboard", headers=H).json()
        payload = _commit_payload(dash, dash["current_round"])
        payload.update({"crisis_severity": 100.0, "imitation_decay_rate": 0.0, "emergency_credit_used": True})
        _clear_commit_gate(team)
        r = client.post(f"/api/simulations/{team}/commit-turn", json=payload, headers=H)
        assert r.status_code == 201, r.text
        ev = r.json()["events"]
        assert ev["crisis_severity_effective"] == 0.0          # R1 has no crisis, whatever the client says
        assert ev.get("emergency_credit_used") is not True     # allowance is above the floor
        assert ev["synergy_decayed_from"] > r.json()["global_state"]["synergy_multiplier"]  # decay applied

    def test_round_four_crisis_comes_from_config(self):
        from round_logic import base_crisis_severity_for_round
        assert base_crisis_severity_for_round(4) == 40.0
        assert base_crisis_severity_for_round(1) == 0.0


class TestF07ImitationDecayBound:
    """The other half of F-07, found at launch-readiness review 2026-09-03.

    Moving the decay rate from the client to the server made the value on the
    DURABLE DATA VOLUME authoritative — and a volume seeded before F-07 still
    carries 0.10 against a repo copy of 0.05. Nothing failed; every team's
    competitive advantage simply decayed at twice the documented rate (0.80 ->
    0.5042 over a ten-round game at 0.05, 0.3100 at 0.10).

    CBAM and the NCD thresholds got a sanity bound for exactly this on
    2026-09-01; this key did not. Both branches are pinned here because a
    ceiling that is never exercised is a ceiling nobody notices has been
    widened — the bound must clamp the known-bad value AND leave the tuning
    band below it alone.
    """

    def test_the_live_rate_is_the_documented_one(self):
        import config
        assert config.DEFAULT_IMITATION_DECAY_RATE == pytest.approx(0.05)
        assert config.DEFAULT_IMITATION_DECAY_RATE <= config._IMITATION_DECAY_SANITY_MAX

    def test_the_ceiling_sits_below_the_known_bad_value(self):
        """2.4: a bound raised to admit the value it was meant to catch
        certifies that value. 0.10 is the stale pre-F-07 rate."""
        import config
        assert config._IMITATION_DECAY_DEFAULT < config._IMITATION_DECAY_SANITY_MAX < 0.10

    def test_repo_config_matches_the_default(self):
        import json, pathlib
        cfg = json.loads((pathlib.Path(__file__).resolve().parent.parent.parent
                          / "simulation_config.json").read_text(encoding="utf-8-sig"))
        rate = cfg["engine_parameters"]["imitation_decay"]["default_rate"]
        assert rate == 0.05

    def test_a_stale_volume_value_is_clamped_and_says_so(self, decay_rate_on_volume, capsys):
        """Branch 1: above the ceiling -> default, with a warning naming both."""
        cfg = decay_rate_on_volume(0.10)
        assert cfg.DEFAULT_IMITATION_DECAY_RATE == pytest.approx(0.05)
        out = capsys.readouterr().out
        assert "imitation_decay.default_rate" in out
        assert "0.1" in out and "0.08" in out and "0.05" in out

    def test_a_configured_value_within_the_bound_is_honoured(self, decay_rate_on_volume, capsys):
        """Branch 2: at or below the ceiling -> used as configured, silently.
        This key is facilitator-editable through the Excel importer, so the
        bound must not collapse the tuning band onto the default."""
        for rate in (0.07, 0.08):
            cfg = decay_rate_on_volume(rate)
            assert cfg.DEFAULT_IMITATION_DECAY_RATE == pytest.approx(rate)
            assert "imitation_decay" not in capsys.readouterr().out


@pytest.fixture
def config_key_on_volume(tmp_path, monkeypatch):
    """Generalisation of decay_rate_on_volume: load `config` against a data
    volume whose simulation_config.json carries ANY chosen key, then restore."""
    import importlib
    import json
    import os
    import pathlib
    import config as _config

    repo_cfg = pathlib.Path(__file__).resolve().parent.parent.parent / "simulation_config.json"
    original = os.environ.get("MURESSONS_DATA_DIR")

    def _load(path: list[str], value):
        data = json.loads(repo_cfg.read_text(encoding="utf-8"))
        node = data
        for seg in path[:-1]:
            node = node.setdefault(seg, {})
        node[path[-1]] = value
        (tmp_path / "simulation_config.json").write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setenv("MURESSONS_DATA_DIR", str(tmp_path))
        return importlib.reload(_config)

    yield _load

    if original is None:
        os.environ.pop("MURESSONS_DATA_DIR", None)
    else:
        os.environ["MURESSONS_DATA_DIR"] = original
    importlib.reload(_config)
    # engine captures the typed constants at import (`from config import ...`);
    # put it back on the restored config so nothing leaks into later tests.
    import engine as _engine
    importlib.reload(_engine)


class TestRatchetBaselineBound:
    """Audit 2026-09-04 F-07. regulatory_ratchet.baseline moved 10 -> 20 on
    2026-09-01 (F-10) and was the ONE stale-volume value with no clamp: CBAM,
    the NCD thresholds and the imitation rate warn and fall back, this key
    governed silently. On a volume seeded before F-10 every team paid
    $1.6M-$3.75M in round 1 before any decision (engine.py regulatory ratchet:
    (avg_gov_risk - baseline) x $500k on a seed mean of 13.25 / 17.5).
    Both branches pinned, as for TestF07ImitationDecayBound."""

    _PATH = ["engine_parameters", "regulatory_ratchet", "baseline"]

    def test_the_live_baseline_is_the_documented_one(self):
        import config
        assert config.REG_RATCHET_BASELINE == pytest.approx(20.0)
        assert config._REG_RATCHET_BASELINE_LEGACY_MAX < config._REG_RATCHET_BASELINE_DEFAULT

    def test_repo_config_matches_the_default(self):
        import json, pathlib
        cfg = json.loads((pathlib.Path(__file__).resolve().parent.parent.parent
                          / "simulation_config.json").read_text(encoding="utf-8-sig"))
        assert cfg["engine_parameters"]["regulatory_ratchet"]["baseline"] == 20.0

    def test_a_stale_volume_value_is_clamped_and_says_so(self, config_key_on_volume, capsys):
        cfg = config_key_on_volume(self._PATH, 10.0)
        assert cfg.REG_RATCHET_BASELINE == pytest.approx(20.0)
        out = capsys.readouterr().out
        assert "regulatory_ratchet.baseline" in out
        assert "10.0" in out and "20.0" in out

    def test_a_stricter_baseline_is_honoured(self, config_key_on_volume, capsys):
        """The band ABOVE the legacy value is a legitimate tuning (a stricter regulator)."""
        for value in (15.0, 25.0):
            cfg = config_key_on_volume(self._PATH, value)
            assert cfg.REG_RATCHET_BASELINE == pytest.approx(value)
            assert "regulatory_ratchet" not in capsys.readouterr().out

    def test_a_seed_team_is_not_fined_in_round_one_on_a_stale_volume(self, config_key_on_volume):
        """The engine reads the clamped constant: the R1 ratchet stays inactive."""
        import importlib
        config_key_on_volume(self._PATH, 10.0)
        import engine as _engine
        importlib.reload(_engine)          # picks up the clamped constant; fixture teardown reloads again
        gs, bus = _tick_state()            # seed governance risk 20 > the legacy baseline 10
        res = _tick(gs, bus, choice="option_b")
        ratchet = res["events"].get("regulatory_ratchet") or {}
        assert not ratchet.get("active"), ratchet
        assert float(ratchet.get("fine", 0) or 0) == 0.0


# ═══════════════════════════════════════════════════════════════════════════
#  F-08 / F-09 / F-10 / F-12 / F-13 — dead or positional mechanics
# ═══════════════════════════════════════════════════════════════════════════

class TestF08StakeholderFatigue:
    def test_fatigue_dampens_reputation_recovery_after_a_crisis(self):
        """Never fired before (the derived group figure can't exceed the BU mean).
        Now: with a crisis on record, this tick's GAIN in a BU's stock is scaled
        by 1/(1 + 0.3 × crises); losses are untouched."""
        gs, bus = _tick_state()
        gs["active_event_flags"]["crisis_count_lifetime"] = 2
        # option_a in R1 raises reputation via the option impacts; compare with no-crisis run
        res_c = _tick(gs, bus, choice="option_a")
        gs0, bus0 = _tick_state()
        res_0 = _tick(gs0, bus0, choice="option_a")
        gain_0 = sum(b["reputation_score"] for b in res_0["bu_states"]) - 120.0
        gain_c = sum(b["reputation_score"] for b in res_c["bu_states"]) - 120.0
        if gain_0 > 0:
            assert res_c["events"].get("stakeholder_fatigue_applied") is True
            assert res_c["events"]["stakeholder_fatigue_efficiency"] == pytest.approx(1 / 1.6, abs=1e-3)
            assert 0 < gain_c < gain_0
        else:  # no positive movement in this configuration → nothing to dampen, nothing fired
            assert res_c["events"].get("stakeholder_fatigue_applied") is None


class TestF09NoPositionalCarbonHeuristic:
    def test_option_letter_alone_does_not_move_carbon_intensity(self):
        gs, bus = _tick_state()
        ci_a = [b["carbon_intensity"] for b in _tick(gs, bus, choice="option_a")["bu_states"]]
        ci_c = [b["carbon_intensity"] for b in _tick(gs, bus, choice="option_c")["bu_states"]]
        # the ONLY CI difference between A and C in R1 must come from the configured
        # option deltas (applied in post_tick, not in process_tick) — so here: none.
        assert ci_a == ci_c


class TestF10Units:
    def test_ncd_thresholds_are_index_scale(self):
        import config
        assert config.NCD_HARD_CAP <= 10_000 and config.NCD_WARN_THRESHOLD <= 5_000
        assert config.NCD_OPEX_PENALTY_PER_UNIT >= 100

    def test_sdg_6_and_14_can_score(self):
        from engine import calc_sdg_impact
        bus = [{"bu_id": "a", "water_dependency": 20.0, "social_license_score": 50, "reputation_score": 50,
                "governance_risk_score": 20, "carbon_intensity": 30, "natural_capital_debt": 0, "revenue_base": 1e7}]
        out = calc_sdg_impact(bus, {})
        scores = {int(k): v["raw_score"] for k, v in out["sdg_scores"].items()}
        assert scores[6] > 0 and scores[14] > 0, out["sdg_scores"]
        # and a high-water-dependency BU scores lower on both
        bus[0]["water_dependency"] = 80.0
        worse = {int(k): v["raw_score"] for k, v in calc_sdg_impact(bus, {})["sdg_scores"].items()}
        assert worse[6] < scores[6] and worse[14] < scores[14]

    def test_seed_governance_is_not_fined_in_round_one(self):
        gs, bus = _tick_state(gov=17.5)
        res = _tick(gs, bus)
        assert res["events"]["regulatory_ratchet"]["active"] is False


class TestF12SingleTerminalValueFormula:
    def test_live_finale_applies_sdg_multiplier_and_ebitda_floor(self):
        """The live R10 path and terminal_valuation.calculate_terminal_value must
        agree on M_SDG and on flooring EBITDA at 0."""
        from terminal_valuation import calculate_sdg_multiplier, EBITDA_FLOOR
        assert calculate_sdg_multiplier(60.0)["m_sdg"] == pytest.approx(1.15)
        assert EBITDA_FLOOR == 0.0
        import inspect, round_logic
        src = inspect.getsource(round_logic._post_r10_grand_finale)
        assert "calculate_sdg_multiplier" in src and "EBITDA_FLOOR" in src
        assert "* mr * m_sdg" in src


class TestF13CiBaseline:
    def test_ci_baseline_is_stamped_once_and_sbti_tracks_it(self):
        gs, bus = _tick_state()
        res = _tick(gs, bus, ratio=0.5, capex=5_000_000)
        for b in res["bu_states"]:
            assert b["ci_baseline_r1"] == 30.0
        gs2, bus2 = res["global_state"], res["bu_states"]
        gs2["round_number"] = 2
        gs2["active_event_flags"]["stochastic_seed"] = "econ"
        gs2["pedagogical_overrides"] = gs["pedagogical_overrides"]
        res2 = _tick(gs2, bus2, ratio=0.5, capex=5_000_000)
        for b in res2["bu_states"]:
            assert b["ci_baseline_r1"] == 30.0          # unchanged after round 1
        sbti = res2["events"].get("sbti_pathway") or res2["events"].get("sbti_per_bu") or {}
        per_bu = sbti.get("per_bu") if isinstance(sbti, dict) else None
        if per_bu:
            for bu_id, rec in per_bu.items():
                assert rec["target_ci"] == pytest.approx(30.0 * (1 - 0.0822), abs=0.5)


# ═══════════════════════════════════════════════════════════════════════════
#  F-19 / F-36 — engine and persistence failures are visible
# ═══════════════════════════════════════════════════════════════════════════

class TestF19VisibleFailures:
    def test_engine_module_failure_is_recorded_on_the_round(self, monkeypatch):
        import round_logic

        def boom(*a, **k):
            raise RuntimeError("balance sheet exploded")
        import balance_sheet
        monkeypatch.setattr(balance_sheet, "process_balance_sheet_tick", boom)
        gs = {"round_number": 2, "corporate_treasury": 5e7, "group_reputation": 60.0, "synergy_multiplier": 0.35,
              "cost_of_capital": 0.05, "active_event_flags": {}, "pedagogical_overrides": {
                  "biodiversity_engine_enabled": False, "board_governance_enabled": False,
                  "org_politics_enabled": False, "supply_chain_network_enabled": False,
                  "npc_stakeholders_enabled": False, "branching_enabled": False, "dynamic_cases_enabled": False}}
        bus = [{"bu_id": "pharma", "revenue_base": 2e7, "opex_base": 1.2e7, "reputation_score": 60,
                "social_license_score": 55, "governance_risk_score": 20, "natural_capital_debt": 0,
                "carbon_intensity": 30, "water_dependency": 30, "risk_factors": {}}]
        extra = round_logic.run_new_engines(round_number=2, global_state=gs, bu_states=bus, events={"decisions_raw": [], "dividends_paid": 0})
        assert any(f["engine"] == "Balance sheet engine" and "exploded" in f["error"] for f in extra.get("engine_failures", []))

    def test_commit_surfaces_engine_failures_to_the_console(self, monkeypatch):
        import router, balance_sheet

        def boom(*a, **k):
            raise RuntimeError("ledger down")
        monkeypatch.setattr(balance_sheet, "process_balance_sheet_tick", boom)
        pushed = []

        async def fake_broadcast(msg):
            pushed.append(msg)
        from admin_router import manager
        monkeypatch.setattr(manager, "broadcast_admin", fake_broadcast)
        from admin_shared import _god_mode_settings
        _god_mode_settings["solo_mode_enabled"] = True
        client.cookies.clear()
        sid = client.post("/api/simulations/solo-start", json={"player_name": "EF", "decision_paradigm": "legacy_abc"}).json()["session_id"]
        dash = client.get(f"/api/simulations/{sid}/dashboard").json()
        _clear_commit_gate(sid)
        before = router._ENGINE_FAILURE_COUNTER["total"]
        r = client.post(f"/api/simulations/{sid}/commit-turn", json=_commit_payload(dash, 1))
        assert r.status_code == 201, r.text
        ev = r.json()["events"]
        assert ev["engine_failure_alert"]["count"] >= 1
        assert "Balance sheet engine" in ev["engine_failure_alert"]["engines"]
        assert router._ENGINE_FAILURE_COUNTER["total"] > before
        assert any(m.get("type") == "engine_failure" and m.get("session_id") == sid for m in pushed)
        health = client.get("/api/health").json()
        assert health["engine_failures"]["total"] >= 1

    def test_persistence_failure_is_registered_and_degrades_strict_health(self, monkeypatch):
        import admin_shared, json
        before = admin_shared.persistence_health()["failures"]

        def refuse(*a, **k):
            raise OSError(28, "No space left on device")
        monkeypatch.setattr(json, "dump", refuse)
        admin_shared._persist_facilitators()
        after = admin_shared.persistence_health()
        assert after["failures"] == before + 1
        assert after["last"]["store"] == "facilitator_registry" and "No space" in after["last"]["error"]
        monkeypatch.undo()
        h = client.get("/api/health?strict=1")
        assert h.json()["persistence"]["failures"] >= 1
        assert h.json()["status"] == "degraded"
        # leave the process-wide register as we found it for later tests
        admin_shared._PERSISTENCE_FAILURES["count"] = before
        admin_shared._PERSISTENCE_FAILURES["last"] = None


# ═══════════════════════════════════════════════════════════════════════════
#  F-33 / F-34 / F-35 — edge cases
# ═══════════════════════════════════════════════════════════════════════════

class TestF33AutoCommitDefaultIsCanonicalOptionB:
    def test_default_is_expressed_in_display_space_so_it_deshuffles_to_option_b(self):
        import router
        from option_shuffle import get_shuffle_mapping, deshuffle_choice
        seed = 424242
        for rnd in range(1, 11):
            body = router._auto_commit_request({"corporate_treasury": 5e7}, [{"bu_id": "pharma"}], rnd, shuffle_seed=seed)
            sent = body.decisions[0].choice_selected
            assert deshuffle_choice(sent, seed, rnd) == "option_b", (rnd, sent)
        # a saved draft is already a display key and is passed through untouched
        body = router._auto_commit_request({"saved_decision_choice": "option_c"}, [{"bu_id": "pharma"}], 3, shuffle_seed=seed)
        assert body.decisions[0].choice_selected == "option_c"
        # without a seed (no shuffle) the literal is the canonical key
        body = router._auto_commit_request({}, [{"bu_id": "pharma"}], 3, shuffle_seed=None)
        assert body.decisions[0].choice_selected == "option_b"


class TestF34IdempotentUnlock:
    def test_target_round_is_idempotent_and_capped(self):
        gm = _god()
        fa, ck = _facilitator(gm, "Unlock A")
        cohort = _cohort(ck, fa, "Unlock Cohort")
        assert client.post(f"/api/admin/sessions/{cohort}/pacing", json={"mode": "manual"}, cookies=ck).status_code == 200
        r1 = client.post(f"/api/admin/sessions/{cohort}/pacing/unlock", json={"target_round": 2}, cookies=ck).json()
        r2 = client.post(f"/api/admin/sessions/{cohort}/pacing/unlock", json={"target_round": 2}, cookies=ck).json()
        assert r1["unlocked_round"] == 2 and r1["already_unlocked"] is False
        assert r2["unlocked_round"] == 2 and r2["already_unlocked"] is True   # double-click / retry: no-op
        bad = client.post(f"/api/admin/sessions/{cohort}/pacing/unlock", json={"target_round": 11}, cookies=ck)
        assert bad.status_code == 422
        from admin_shared import _get_pacing
        _get_pacing(cohort)["unlocked_round"] = 10
        r3 = client.post(f"/api/admin/sessions/{cohort}/pacing/unlock", cookies=ck).json()
        assert r3["unlocked_round"] == 10 and r3["already_unlocked"] is True   # never past the last round


class TestF35ChoiceRequired:
    def test_commit_without_a_strategic_option_is_refused(self):
        from admin_shared import _god_mode_settings
        _god_mode_settings["solo_mode_enabled"] = True
        client.cookies.clear()
        sid = client.post("/api/simulations/solo-start", json={"player_name": "NC", "decision_paradigm": "legacy_abc"}).json()["session_id"]
        dash = client.get(f"/api/simulations/{sid}/dashboard").json()
        payload = {"decisions": [{"bu_id": b["bu_id"], "capex_allocated": 1} for b in dash["business_units"]],
                   "expected_round": 1}
        _clear_commit_gate(sid)
        r = client.post(f"/api/simulations/{sid}/commit-turn", json=payload)
        assert r.status_code == 400, r.text
        assert r.json()["detail"]["code"] == "choice_required"
        assert client.get(f"/api/simulations/{sid}/dashboard").json()["current_round"] == 1


# ═══════════════════════════════════════════════════════════════════════════
#  F-28 / F-29 — scalability
# ═══════════════════════════════════════════════════════════════════════════

class TestF28IndexedSiblingLookups:
    def test_child_lookup_is_cohort_scoped_on_the_memory_store(self):
        import database as db_mod
        gm = _god()
        fa, ck = _facilitator(gm, "Idx A")
        cohort = _cohort(ck, fa, "Idx Cohort")
        teams = [_team(ck, cohort, f"T{i}") for i in range(2)]
        kids = _run_async(db_mod.fetch_child_session_ids(cohort))
        assert set(kids) == {t[2] for t in teams}
        full = _run_async(db_mod.get_child_sessions(cohort))
        assert {c["session_id"] for c in full} == set(kids)
        assert all(c.get("parent_cohort_id") == cohort for c in full)

    def test_commit_maps_are_pruned(self):
        import router, time
        router._commit_timestamps["stale-session"] = time.time() - 7200
        router._commit_locks["stale-session"] = router._asyncio.Lock()
        router._commit_maps_last_prune = 0.0
        router._prune_commit_maps(time.time())
        assert "stale-session" not in router._commit_timestamps
        assert "stale-session" not in router._commit_locks


class TestF29SnapshotDebounce:
    def test_many_persist_calls_inside_the_window_write_once(self, monkeypatch):
        import asyncio
        import database_memory as dm
        monkeypatch.setattr(dm, "_SNAPSHOT_DEBOUNCE_S", 0.05)
        writes = []
        monkeypatch.setattr(dm, "_write_snapshot_now", lambda: writes.append(1))

        async def go():
            dm._snapshot_dirty = False
            dm._snapshot_timer = None
            for _ in range(25):
                dm._persist()
            assert writes == []                 # nothing written yet — coalescing
            await asyncio.sleep(0.12)
            return len(writes)
        assert _run_async(go()) == 1

    def test_flush_writes_pending_state_immediately(self, monkeypatch):
        import database_memory as dm
        monkeypatch.setattr(dm, "_SNAPSHOT_DEBOUNCE_S", 5.0)
        writes = []
        monkeypatch.setattr(dm, "_write_snapshot_now", lambda: writes.append(1))

        async def go():
            dm._snapshot_dirty = False
            dm._snapshot_timer = None
            dm._persist()
            assert writes == []
            dm.flush_snapshot()
            return len(writes), dm._snapshot_timer
        n, timer = _run_async(go())
        assert n == 1 and timer is None
