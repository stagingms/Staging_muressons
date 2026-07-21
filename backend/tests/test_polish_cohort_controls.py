"""LOW-tier / polish cohort controls — accessibility profile, white-label
branding, data retention & compliance (consent + export), and webhooks.

Pins:
  1. All polish controls are real, overridable, effective settings whose
     defaults preserve legacy behaviour exactly.
  2. The normaliser sanitises hostile input: font scale clamped, non-https
     logo/webhook URLs rejected, malformed hex colours dropped.
  3. Consent is enforced server-side at join when (and only when) required,
     and the acceptance timestamp lands on the player session.
  4. The retention reaper removes only opted-in, expired cohorts (children
     included) and never touches open-ended or default cohorts.
  5. export-my-data returns session metadata + history without credentials.
  6. Webhook scheduling is inert without config and never raises.
"""

import asyncio
from datetime import date

import database_memory as dbm
from admin_shared import (
    _god_mode_settings,
    COHORT_OVERRIDABLE_KEYS,
    cohort_settings,
    normalize_advanced_cohort_settings as normalize,
)

_POLISH_KEYS = [
    "accessibility_defaults", "branding_institution", "branding_logo_url",
    "branding_primary_color", "data_retention_days", "consent_required",
    "consent_text", "webhook_url",
]


# ── Config model ─────────────────────────────────────────────────────────────

def test_every_polish_control_has_a_default_and_is_overridable():
    for k in _POLISH_KEYS:
        assert k in _god_mode_settings, f"missing default: {k}"
        assert k in COHORT_OVERRIDABLE_KEYS, f"not per-cohort overridable: {k}"


def test_polish_defaults_preserve_legacy_behaviour():
    acc = _god_mode_settings["accessibility_defaults"]
    assert acc["high_contrast"] is False and acc["font_scale"] == 1.0
    assert _god_mode_settings["branding_institution"] == ""
    assert _god_mode_settings["data_retention_days"] == 0   # keep forever
    assert _god_mode_settings["consent_required"] is False
    assert _god_mode_settings["webhook_url"] == ""


# ── Normalisation ────────────────────────────────────────────────────────────

def test_accessibility_profile_is_sanitised():
    out = normalize({"accessibility_defaults": {
        "high_contrast": 1, "font_scale": 99, "reduced_motion": "yes",
        "colorblind_safe": 0, "screen_reader_mode": True, "junk_key": "drop-me",
    }})["accessibility_defaults"]
    assert out["high_contrast"] is True
    assert out["font_scale"] == 1.6            # clamped
    assert out["reduced_motion"] is True
    assert out["colorblind_safe"] is False
    assert out["screen_reader_mode"] is True
    assert "junk_key" not in out               # unknown keys dropped
    assert normalize({"accessibility_defaults": "garbage"})["accessibility_defaults"]["font_scale"] == 1.0
    assert normalize({"accessibility_defaults": {"font_scale": 0.1}})["accessibility_defaults"]["font_scale"] == 0.8


def test_branding_is_sanitised():
    assert normalize({"branding_institution": "  IIM Ahmedabad  "})["branding_institution"] == "IIM Ahmedabad"
    assert normalize({"branding_logo_url": "https://x.edu/logo.png"})["branding_logo_url"] == "https://x.edu/logo.png"
    assert normalize({"branding_logo_url": "http://insecure.com/l.png"})["branding_logo_url"] == ""
    assert normalize({"branding_logo_url": "javascript:alert(1)"})["branding_logo_url"] == ""
    assert normalize({"branding_primary_color": "#1E90FF"})["branding_primary_color"] == "#1E90FF"
    assert normalize({"branding_primary_color": "red"})["branding_primary_color"] == ""
    assert normalize({"branding_primary_color": "#12345"})["branding_primary_color"] == ""


def test_retention_and_webhook_are_sanitised():
    assert normalize({"data_retention_days": 99999})["data_retention_days"] == 3650
    assert normalize({"data_retention_days": -1})["data_retention_days"] == 0
    assert normalize({"webhook_url": "https://lms.example.com/hook"})["webhook_url"] == "https://lms.example.com/hook"
    assert normalize({"webhook_url": "http://plain.example.com"})["webhook_url"] == ""
    assert normalize({"consent_required": 1})["consent_required"] is True
    assert len(normalize({"consent_text": "x" * 5000})["consent_text"]) == 2000


# ── Consent enforcement at join ──────────────────────────────────────────────

_PARENT = "cohort-polish-consent"


def _setup_cohort():
    dbm._sessions[_PARENT] = {
        "parent_cohort_id": None,
        "player_name": "POLISH COHORT",
        "cohort_name": "POLISH COHORT",
        "allowed_player_ids": ["PL-1"],
        "registered_players": [{"player_id": "PL-1", "name": "Polish Player", "password": ""}],
    }
    dbm._global_states[_PARENT] = [{
        "corporate_treasury": 30e6, "group_reputation": 55,
        "round_number": 1, "synergy_multiplier": 1.0, "active_event_flags": {},
    }]


def _teardown_cohort():
    for sid in list(dbm._sessions):
        if sid == _PARENT or dbm._sessions[sid].get("parent_cohort_id") == _PARENT:
            dbm._sessions.pop(sid, None)
            dbm._global_states.pop(sid, None)
    cohort_settings.pop(_PARENT, None)
    from router import _session_players
    _session_players.pop(_PARENT, None)


def _join(consent=False):
    from fastapi import HTTPException
    from router import join_session, JoinSessionRequest
    try:
        return asyncio.run(join_session(
            _PARENT, JoinSessionRequest(player_id="PL-1", password="", consent=consent))), None
    except HTTPException as e:
        return None, e


def test_consent_not_required_by_default():
    _setup_cohort()
    try:
        res, err = _join(consent=False)
        assert err is None
        assert "session_id" in res
    finally:
        _teardown_cohort()


def test_consent_enforced_and_timestamped_when_required():
    _setup_cohort()
    cohort_settings[_PARENT] = {"consent_required": True, "consent_text": "You agree to X."}
    try:
        _, err = _join(consent=False)
        assert err is not None and err.status_code == 403
        assert "You agree to X." in str(err.detail)
        res, err2 = _join(consent=True)
        assert err2 is None
        psess = dbm._sessions[res["session_id"]]
        assert psess.get("consent_given_at"), "consent timestamp must be recorded"
    finally:
        _teardown_cohort()


# ── Data retention reaper ────────────────────────────────────────────────────

def test_retention_reaps_only_opted_in_expired_cohorts():
    from session_reaper import reap_once
    dbm._sessions["cohort-ret-expired"] = {
        "parent_cohort_id": None, "end_date": "2026-01-01", "player_name": "C1"}
    dbm._sessions["player-ret-child"] = {
        "parent_cohort_id": "cohort-ret-expired", "player_id": "p1"}
    dbm._sessions["cohort-ret-default"] = {          # no retention configured
        "parent_cohort_id": None, "end_date": "2026-01-01", "player_name": "C2"}
    dbm._sessions["cohort-ret-open"] = {             # retention set, but no end_date
        "parent_cohort_id": None, "player_name": "C3"}
    cohort_settings["cohort-ret-expired"] = {"data_retention_days": 30}
    cohort_settings["cohort-ret-open"] = {"data_retention_days": 30}
    try:
        summary = reap_once(today=date(2026, 7, 17))  # well past 2026-01-31
        assert summary["retention_cohorts_reaped"] == 1
        assert "cohort-ret-expired" not in dbm._sessions
        assert "player-ret-child" not in dbm._sessions     # children go with parent
        assert "cohort-ret-default" in dbm._sessions       # 0 days ⇒ keep forever
        assert "cohort-ret-open" in dbm._sessions          # no end_date ⇒ never reaped
        assert "cohort-ret-expired" not in cohort_settings # overlay cleaned too
    finally:
        for sid in ("cohort-ret-expired", "player-ret-child", "cohort-ret-default", "cohort-ret-open"):
            dbm._sessions.pop(sid, None)
        cohort_settings.pop("cohort-ret-open", None)
        cohort_settings.pop("cohort-ret-expired", None)


def test_retention_not_reaped_inside_window():
    from session_reaper import reap_once
    dbm._sessions["cohort-ret-recent"] = {
        "parent_cohort_id": None, "end_date": "2026-07-10", "player_name": "C4"}
    cohort_settings["cohort-ret-recent"] = {"data_retention_days": 30}
    try:
        summary = reap_once(today=date(2026, 7, 17))  # only 7 days after end
        assert summary["retention_cohorts_reaped"] == 0
        assert "cohort-ret-recent" in dbm._sessions
    finally:
        dbm._sessions.pop("cohort-ret-recent", None)
        cohort_settings.pop("cohort-ret-recent", None)


# ── Data export ──────────────────────────────────────────────────────────────

def test_export_my_data_returns_history_without_credentials(monkeypatch):
    import router as router_mod

    async def _fake_owner_check(request, sid):
        return None

    async def _fake_info(sid):
        return {"session_id": sid, "player_name": "Exporter", "password": "SECRET",
                "consent_given_at": "2026-07-01T00:00:00+00:00",
                "allowed_player_ids": ["a"], "_internal": "hidden"}

    async def _fake_history(sid):
        return [{"round_number": 1, "global_state": {"corporate_treasury": 1.0}}]

    monkeypatch.setattr(router_mod, "_assert_player_owns_session", _fake_owner_check)
    monkeypatch.setattr(router_mod.db, "get_session_info", _fake_info)
    monkeypatch.setattr(router_mod.db, "fetch_round_history", _fake_history)

    res = asyncio.run(router_mod.export_my_data("sess-x", request=None))
    assert res["export_version"] == 1
    assert res["session"]["player_name"] == "Exporter"
    assert "password" not in res["session"]
    assert "allowed_player_ids" not in res["session"]
    assert "_internal" not in res["session"]
    assert res["round_history"][0]["round_number"] == 1
    assert res["consent_given_at"] == "2026-07-01T00:00:00+00:00"


# ── Webhooks ─────────────────────────────────────────────────────────────────

def test_webhook_inert_without_config_and_never_raises():
    from webhook_util import fire_webhook, resolve_webhook_url
    assert resolve_webhook_url("no-such-cohort") == ""
    # No URL configured ⇒ nothing scheduled, no exception.
    assert fire_webhook("round_committed", "no-such-cohort") is False


def test_webhook_resolves_parent_scoped_url_and_requires_loop():
    from webhook_util import fire_webhook, resolve_webhook_url
    cohort_settings["cohort-hook"] = {"webhook_url": "https://lms.example.com/hook"}
    try:
        assert resolve_webhook_url("child-sess", "cohort-hook") == "https://lms.example.com/hook"
        # Configured but called from a sync context (no running loop) ⇒ False, no raise.
        assert fire_webhook("round_committed", "child-sess", "cohort-hook") is False

        async def _in_loop():
            return fire_webhook("game_over", "child-sess", "cohort-hook",
                                payload={"round_number": 10, "game_over": True})
        # Inside a loop the task is scheduled (delivery itself is best-effort).
        assert asyncio.run(_in_loop()) is True
    finally:
        cohort_settings.pop("cohort-hook", None)
