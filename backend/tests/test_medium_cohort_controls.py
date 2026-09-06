"""MEDIUM-tier cohort controls — timers/timezone, join-code enforcement,
report-access controls, and clone-as-template.

Pins:
  1. The four control groups are real, overridable, effective cohort settings
     with fail-open defaults (an unconfigured cohort behaves exactly as before).
  2. The normaliser coerces/clamps hostile input (bad timezone, out-of-range
     timer, unknown policy strings).
  3. Join-code + late-join policy are enforced SERVER-SIDE at the join endpoint
     (rejoin is never blocked).
  4. report_access gates the player final-report payload server-side.
  5. Templates round-trip: save a cohort's overrides → apply to a fresh cohort
     through the same normalised PATCH path; transient freeze state never
     leaks into a template.
"""

import asyncio

import pytest

import database_memory as dbm
from admin_shared import (
    _god_mode_settings,
    COHORT_OVERRIDABLE_KEYS,
    cohort_settings,
    get_effective_settings,
    normalize_advanced_cohort_settings as normalize,
    _cohort_templates,
)

_MEDIUM_KEYS = ["cohort_timezone", "late_join_policy", "report_access"]


# ── Config model ─────────────────────────────────────────────────────────────

def test_every_medium_control_has_a_default_and_is_overridable():
    for k in _MEDIUM_KEYS:
        assert k in _god_mode_settings, f"missing default: {k}"
        assert k in COHORT_OVERRIDABLE_KEYS, f"not per-cohort overridable: {k}"


def test_medium_defaults_preserve_legacy_behaviour():
    assert _god_mode_settings["cohort_timezone"] == ""
    assert _god_mode_settings["late_join_policy"] == "anytime"
    assert _god_mode_settings["report_access"] == "full"
    # Per-round timer reuses the pre-existing pedagogical toggles — still off/300s.
    from pedagogical_engine import DEFAULT_PEDAGOGICAL_TOGGLES
    assert DEFAULT_PEDAGOGICAL_TOGGLES["decision_timer_enabled"] is False
    assert DEFAULT_PEDAGOGICAL_TOGGLES["decision_timer_seconds"] == 300


# ── Normalisation ────────────────────────────────────────────────────────────

def test_round_timer_is_clamped():
    assert normalize({"decision_timer_seconds": 999999})["decision_timer_seconds"] == 7200
    assert normalize({"decision_timer_seconds": -5})["decision_timer_seconds"] == 30
    assert normalize({"decision_timer_seconds": "abc"})["decision_timer_seconds"] == 300


def test_policy_enums_fall_back_safely():
    assert normalize({"late_join_policy": "sneaky"})["late_join_policy"] == "anytime"
    assert normalize({"late_join_policy": "closed"})["late_join_policy"] == "closed"
    assert normalize({"report_access": "everything!!"})["report_access"] == "full"
    assert normalize({"report_access": "facilitator_only"})["report_access"] == "facilitator_only"


def test_timezone_is_validated_against_iana_db():
    assert normalize({"cohort_timezone": "Asia/Kolkata"})["cohort_timezone"] == "Asia/Kolkata"
    assert normalize({"cohort_timezone": "  Europe/London "})["cohort_timezone"] == "Europe/London"
    assert normalize({"cohort_timezone": "Mars/Olympus_Mons"})["cohort_timezone"] == ""
    assert normalize({"cohort_timezone": ""})["cohort_timezone"] == ""


# ── Join enforcement (server-side) ───────────────────────────────────────────

_PARENT = "cohort-med-join"
_REG = {"player_id": "PM-1", "name": "Med Player", "password": ""}


def _setup_cohort():
    dbm._sessions[_PARENT] = {
        "parent_cohort_id": None,
        "player_name": "MED COHORT",
        "cohort_name": "MED COHORT",
        "allowed_player_ids": ["PM-1", "PM-2"],
        "registered_players": [dict(_REG)],
    }
    dbm._global_states[_PARENT] = [{
        "corporate_treasury": 30e6, "group_reputation": 55,
        "round_number": 1, "synergy_multiplier": 1.0,
        "active_event_flags": {},
    }]


def _teardown_cohort():
    for sid in list(dbm._sessions):
        if sid == _PARENT or dbm._sessions[sid].get("parent_cohort_id") == _PARENT:
            dbm._sessions.pop(sid, None)
            dbm._global_states.pop(sid, None)
    cohort_settings.pop(_PARENT, None)
    from router import _session_players
    _session_players.pop(_PARENT, None)


def _join(join_code=""):
    from fastapi import HTTPException
    from router import join_session, JoinSessionRequest
    req = JoinSessionRequest(player_id="PM-1", password="", join_code=join_code)
    try:
        return asyncio.run(join_session(_PARENT, req)), None
    except HTTPException as e:
        return None, e


def test_join_code_not_required_when_unset():
    _setup_cohort()
    try:
        res, err = _join()
        assert err is None, f"unconfigured cohort must join freely: {getattr(err, 'detail', err)}"
        assert res["status"] in ("joined", "created", "rejoined") or "session_id" in res
    finally:
        _teardown_cohort()


def test_join_code_enforced_when_configured():
    _setup_cohort()
    cohort_settings[_PARENT] = {"join_method": "code", "join_code": "ABC123"}
    try:
        _, err = _join("")
        assert err is not None and err.status_code == 403
        _, err2 = _join("wrong")
        assert err2 is not None and err2.status_code == 403
        res, err3 = _join("  abc123 ")  # trimmed + case-insensitive
        assert err3 is None, getattr(err3, "detail", None)
        assert "session_id" in res
    finally:
        _teardown_cohort()


def test_open_join_method_skips_code_check():
    _setup_cohort()
    cohort_settings[_PARENT] = {"join_method": "open", "join_code": "ABC123"}
    try:
        res, err = _join("")
        assert err is None
        assert "session_id" in res
    finally:
        _teardown_cohort()


def test_closed_cohort_blocks_new_joins_but_not_rejoin():
    _setup_cohort()
    try:
        res, err = _join()  # join while open
        assert err is None
        cohort_settings[_PARENT] = {"late_join_policy": "closed"}
        res2, err2 = _join()  # same player again ⇒ rejoin path, must succeed
        assert err2 is None
        assert res2["status"] == "rejoined"
        # A different (registered) player is a NEW join ⇒ blocked.
        dbm._sessions[_PARENT]["registered_players"].append(
            {"player_id": "PM-2", "name": "Late Player", "password": ""})
        from fastapi import HTTPException
        from router import join_session, JoinSessionRequest
        try:
            asyncio.run(join_session(_PARENT, JoinSessionRequest(player_id="PM-2", password="")))
            assert False, "closed cohort must reject a new join"
        except HTTPException as e:
            assert e.status_code == 403
    finally:
        _teardown_cohort()


def test_before_round_2_blocks_once_cohort_advances():
    _setup_cohort()
    cohort_settings[_PARENT] = {"late_join_policy": "before_round_2"}
    try:
        res, err = _join()  # round 1 everywhere ⇒ allowed
        assert err is None
        # Advance the joined player's session past round 1.
        child_sid = res["session_id"]
        dbm._global_states[child_sid][-1]["round_number"] = 3
        dbm._sessions[_PARENT]["registered_players"].append(
            {"player_id": "PM-2", "name": "Late Player", "password": ""})
        from fastapi import HTTPException
        from router import join_session, JoinSessionRequest
        try:
            asyncio.run(join_session(_PARENT, JoinSessionRequest(player_id="PM-2", password="")))
            assert False, "past round 1 ⇒ before_round_2 must reject"
        except HTTPException as e:
            assert e.status_code == 403
    finally:
        _teardown_cohort()


# ── Report access (server-side) ──────────────────────────────────────────────
# The memory backend's fetch_latest_state rebuilds global_state from an
# allow-list that omits finale keys, so we stub the two db reads the endpoint
# makes — the point under test is the report_access gate, not state storage.

_RP = "cohort-med-report"
_RC = "player-med-report"

_FINALE_STATE = {
    "round_number": 10,
    "global_state": {
        "corporate_treasury": 30e6, "group_reputation": 55,
        "synergy_multiplier": 1.0, "game_over": True,
        # VAL-11c (Wave 3): /final-report derives `terminal_valuation` from the
        # canonical record (nothing ever wrote gs["terminal_valuation"]); the
        # numbers live here, the headline is the narrative that "summary" withholds.
        "final_report_canonical": {"headline": "SECRET NARRATIVE", "terminal_value": 123.0,
                                   "regenerative_multiple": 1.1, "archetype": "pragmatic_operator"},
        "turnaround_amended_report": {"headline": "AMENDED NARRATIVE"},
        "archetype": "pragmatic_operator",
        "active_event_flags": {},
    },
    "bu_states": [],
}


def _final_report(monkeypatch):
    import router as router_mod

    async def _fake_latest(sid):
        return _FINALE_STATE if sid == _RC else None

    async def _fake_info(sid):
        return {"parent_cohort_id": _RP} if sid == _RC else {"parent_cohort_id": None}

    monkeypatch.setattr(router_mod.db, "fetch_latest_state", _fake_latest)
    monkeypatch.setattr(router_mod.db, "get_session_info", _fake_info)

    class _Req:  # F-22: the route now binds the caller; this session is unowned
        headers, cookies, method = {}, {}, "GET"

    return asyncio.run(router_mod.get_final_report(_RC, _Req()))


def test_report_default_full_is_unchanged(monkeypatch):
    try:
        res = _final_report(monkeypatch)
        assert res.get("locked") is not True
        assert res["report_access"] == "full"
        assert res["final_report_canonical"]["headline"] == "SECRET NARRATIVE"
        assert res["terminal_valuation"]["terminal_value"] == 123.0
        assert res["terminal_valuation"]["source"] == "final_report_canonical"
    finally:
        cohort_settings.pop(_RP, None)


def test_report_summary_withholds_narrative_keeps_numbers(monkeypatch):
    cohort_settings[_RP] = {"report_access": "summary"}
    try:
        res = _final_report(monkeypatch)
        assert res["final_report_canonical"] is None
        assert res["turnaround_amended_report"] is None
        assert res["terminal_valuation"]["terminal_value"] == 123.0      # the numbers survive the summary cut
        assert res["archetype"] == "pragmatic_operator"
    finally:
        cohort_settings.pop(_RP, None)


def test_report_facilitator_only_locks_players_out(monkeypatch):
    cohort_settings[_RP] = {"report_access": "facilitator_only"}
    try:
        res = _final_report(monkeypatch)
        assert res["locked"] is True
        assert "terminal_valuation" not in res
        assert "final_report_canonical" not in res
    finally:
        cohort_settings.pop(_RP, None)


# ── Clone-as-template ────────────────────────────────────────────────────────

def test_template_snapshot_roundtrips_through_persistence_helpers():
    from admin_shared import cohort_templates_snapshot, restore_cohort_templates
    _cohort_templates["tpl-test-rt"] = {
        "name": "RT", "settings": {"team_count": 4}, "created_by": "x",
        "source_session_id": "s", "created_at": "now",
    }
    try:
        snap = cohort_templates_snapshot()
        _cohort_templates.clear()
        restore_cohort_templates(snap)
        assert _cohort_templates["tpl-test-rt"]["settings"] == {"team_count": 4}
        # Malformed entries are dropped, never raise.
        restore_cohort_templates({"bad": "not-a-dict", "worse": {"settings": 5}})
        assert "bad" not in _cohort_templates and "worse" not in _cohort_templates
    finally:
        _cohort_templates.pop("tpl-test-rt", None)


def test_save_and_apply_template_end_to_end():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    gm = client.post("/api/admin/facilitators/login",
                     json={"facilitator_id": "god_mode", "password": "sim2026@iim"})
    assert gm.status_code == 200, gm.text

    src, dst = "cohort-tpl-src", "cohort-tpl-dst"
    cohort_settings[src] = {
        "team_count": 7, "quiz_enabled": True, "results_reveal_round": 6,
        "system_frozen": True, "freeze_message": "transient",  # must NOT be templated
    }
    tid = None
    try:
        r = client.post("/api/admin/cohort-templates",
                        json={"name": "Spring Cohort Setup", "source_session_id": src},
                        cookies=gm.cookies)
        assert r.status_code == 200, r.text
        tid = r.json()["template_id"]
        assert r.json()["settings"]["team_count"] == 7
        assert "system_frozen" not in r.json()["settings"]
        assert "freeze_message" not in r.json()["settings"]

        listed = client.get("/api/admin/cohort-templates", cookies=gm.cookies).json()["templates"]
        assert any(t["template_id"] == tid for t in listed)

        r2 = client.post(f"/api/admin/cohort-templates/{tid}/apply/{dst}", cookies=gm.cookies)
        assert r2.status_code == 200, r2.text
        eff = get_effective_settings(dst)
        assert eff["team_count"] == 7
        assert eff["quiz_enabled"] is True
        assert eff["results_reveal_round"] == 6
        assert eff["system_frozen"] is False  # transient state never cloned

        r3 = client.delete(f"/api/admin/cohort-templates/{tid}", cookies=gm.cookies)
        assert r3.status_code == 200
        assert client.delete(f"/api/admin/cohort-templates/{tid}", cookies=gm.cookies).status_code == 404
        tid = None
    finally:
        cohort_settings.pop(src, None)
        cohort_settings.pop(dst, None)
        if tid:
            _cohort_templates.pop(tid, None)


def test_template_from_cohort_with_no_overrides_is_rejected():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    gm = client.post("/api/admin/facilitators/login",
                     json={"facilitator_id": "god_mode", "password": "sim2026@iim"})
    assert gm.status_code == 200, gm.text
    r = client.post("/api/admin/cohort-templates",
                    json={"name": "Empty", "source_session_id": "cohort-that-has-nothing"},
                    cookies=gm.cookies)
    assert r.status_code == 422
