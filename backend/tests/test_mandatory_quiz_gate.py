"""Mandatory-quiz gate + per-player quiz score log.

Facilitator can mark quizzes MANDATORY (quiz_mandatory cohort setting). When on,
a round that carries a quiz notebook blocks the player's commit until they have
taken that round's quiz (≥1 recorded attempt via /learning-bonus). Rounds with
no quiz notebook are unaffected, and the gate is inert when quizzes are off or
the setting is off. Quiz scores are logged per player and surfaced on the final
report for the results / archetype card.

Pins:
  1. quiz_mandatory is a real, overridable, normalised cohort setting (default off).
  2. quiz_gate_status: blocked only when mandatory + enabled + a quiz is due +
     not taken; fails open on the "no quiz this round" case.
  3. commit-turn 403s when the gate is blocked, and succeeds once the quiz is
     taken — the exact "can't decide until quiz done" behaviour.
  4. build_quiz_score_log aggregates the recorded scores with pass/fail.
  5. The final report carries quiz_score_log.
"""

import os

os.environ["USE_MEMORY_DB"] = "true"

from fastapi.testclient import TestClient

import admin_shared
import database_memory as dbm
from admin_shared import _god_mode_settings, COHORT_OVERRIDABLE_KEYS, cohort_settings
from admin_shared import normalize_advanced_cohort_settings as normalize
from main import app
from quiz_gate import quiz_gate_status, build_quiz_score_log, _round_quiz_notebook
from router import _commit_timestamps

client = TestClient(app)


# ── Config model ─────────────────────────────────────────────────────────────

def test_quiz_mandatory_is_a_default_off_overridable_setting():
    assert _god_mode_settings["quiz_mandatory"] is False
    assert "quiz_mandatory" in COHORT_OVERRIDABLE_KEYS
    assert normalize({"quiz_mandatory": 1})["quiz_mandatory"] is True
    assert normalize({"quiz_mandatory": 0})["quiz_mandatory"] is False


# ── Round → quiz notebook resolution (loaded under the test harness) ──────────

def test_every_round_has_a_quiz_notebook():
    # Rounds 1/3/5 come from the seed set; 2/4/6-10 from quiz_banks_rounds — so a
    # mandatory-quiz cohort has a topically-aligned quiz on EVERY round.
    for r in range(1, 11):
        nb = _round_quiz_notebook(r)
        assert nb is not None, f"round {r} has no quiz notebook"
        assert "quiz" in (nb.get("content_types") or [])
        qs = nb.get("quiz_questions") or []
        assert len(qs) >= 10, f"round {r} quiz has only {len(qs)} questions"
        # Every question is well-formed (correct index in range).
        for q in qs:
            assert 0 <= q["correct"] < len(q["options"])


def test_new_round_quizzes_serve_ten_questions():
    # The quiz endpoint returns 10 questions for each newly-scaffolded round.
    for nb_id in ("NLM_R2", "NLM_R4", "NLM_R6", "NLM_R7", "NLM_R8", "NLM_R9", "NLM_R10"):
        r = client.get(f"/api/simulations/quiz/{nb_id}")
        assert r.status_code == 200, r.text
        assert len(r.json()["questions"]) == 10


# ── Gate resolver ────────────────────────────────────────────────────────────

def test_gate_blocks_only_when_mandatory_enabled_due_and_not_taken():
    sid = "cohort-quizgate"
    cohort_settings[sid] = {"quiz_mandatory": True}
    try:
        nb = _round_quiz_notebook(1)
        # Not taken → blocked at round 1 (a quiz is due).
        g = quiz_gate_status("player-x", 1, {"learning_bonuses_awarded": {}}, parent_id=sid)
        assert g["mandatory"] is True
        assert g["required_notebook_id"] == nb["id"]
        assert g["blocked"] is True

        # A round with no quiz notebook is never blocked (rounds 1-10 all have
        # one now, so use an out-of-range round to exercise the "no quiz" path).
        assert _round_quiz_notebook(11) is None
        assert quiz_gate_status("player-x", 11, {"learning_bonuses_awarded": {}}, parent_id=sid)["blocked"] is False

        # Taken (≥1 attempt) → unblocked, best score surfaced.
        gs_taken = {"learning_bonuses_awarded": {f"quiz_complete_{nb['id']}": {"best_score_percent": 90, "attempt": 1, "points": 3000}}}
        g2 = quiz_gate_status("player-x", 1, gs_taken, parent_id=sid)
        assert g2["completed"] is True
        assert g2["best_score_percent"] == 90
        assert g2["blocked"] is False
    finally:
        cohort_settings.pop(sid, None)


def test_gate_inert_when_setting_off():
    sid = "cohort-quizgate-off"
    cohort_settings.pop(sid, None)  # mandatory defaults off
    g = quiz_gate_status("player-y", 1, {"learning_bonuses_awarded": {}}, parent_id=sid)
    assert g["mandatory"] is False
    assert g["blocked"] is False


# ── End-to-end commit gate ───────────────────────────────────────────────────

def _solo():
    r = client.post("/api/simulations/solo-start",
                    json={"player_name": "QZ", "decision_paradigm": "legacy_abc"})
    assert r.status_code in (200, 201), r.text
    return r.json()["session_id"]


def _commit(sid, bus, rnd=1):
    _commit_timestamps[sid] = 0.0
    return client.post(
        f"/api/simulations/{sid}/commit-turn",
        json={
            "decisions": [{
                "bu_id": b["bu_id"], "investment_ratio": 0.5,
                "capex_allocated": 1_000_000, "choice_selected": "option_a",
            } for b in bus],
            "force_override_cfo": True, "expected_round": rnd,
        },
    )


def test_commit_blocked_until_quiz_taken_then_allowed():
    sid = _solo()
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    # Mark THIS solo session's cohort settings mandatory (solo has no parent, so
    # the gate resolves against the session id itself).
    cohort_settings[sid] = {"quiz_mandatory": True}
    try:
        nb = _round_quiz_notebook(1)
        # Round 1 has a quiz notebook; not taken ⇒ commit is blocked (403).
        r_blocked = _commit(sid, bus, 1)
        assert r_blocked.status_code == 403, r_blocked.text
        _detail = r_blocked.json()["detail"].lower()
        assert "complete" in _detail and nb["title"].lower() in _detail

        # Take the quiz (record an attempt via the real endpoint).
        rq = client.post(f"/api/simulations/{sid}/learning-bonus",
                         json={"activity_type": "quiz_complete", "notebook_id": nb["id"], "score_percent": 80})
        assert rq.status_code == 200, rq.text

        # Now the commit succeeds — decisions are unblocked.
        r_ok = _commit(sid, bus, 1)
        assert r_ok.status_code == 201, r_ok.text
    finally:
        cohort_settings.pop(sid, None)


def test_dashboard_surfaces_quiz_gate():
    sid = _solo()
    cohort_settings[sid] = {"quiz_mandatory": True}
    try:
        gs = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]
        assert gs["quiz_gate"]["mandatory"] is True
        assert gs["quiz_gate"]["blocked"] is True   # round 1 quiz not taken yet
    finally:
        cohort_settings.pop(sid, None)


# ── Score log + final report ─────────────────────────────────────────────────

def test_final_report_carries_quiz_score_log():
    sid = _solo()
    nb = _round_quiz_notebook(1)
    # Record a couple of quiz attempts.
    client.post(f"/api/simulations/{sid}/learning-bonus",
                json={"activity_type": "quiz_complete", "notebook_id": nb["id"], "score_percent": 60})
    client.post(f"/api/simulations/{sid}/learning-bonus",
                json={"activity_type": "quiz_complete", "notebook_id": nb["id"], "score_percent": 90})

    # Force the game to a finished state so final-report returns the payload.
    st = dbm._global_states[sid][-1]
    st["round_number"] = 10
    st["game_over"] = True

    r = client.get(f"/api/simulations/{sid}/final-report")
    assert r.status_code == 200, r.text
    log = r.json()["quiz_score_log"]
    assert log is not None
    assert log["quizzes_taken"] == 1
    entry = log["entries"][0]
    assert entry["notebook_id"] == nb["id"]
    assert entry["best_score_percent"] == 90       # best of the two attempts
    assert entry["title"] == nb["title"]
