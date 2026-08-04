"""4.9 — replay(session_id): does a recorded run reproduce from its own record?

This is the tool the last three phases existed to make possible, and therefore
the test that proves they were sufficient. Building it already found one gap:
crisis_severity and decision_paradigm are ENGINE INPUTS the client never sends
— the server derives them — so 4.8's envelope recorded only what was submitted
and left a replay under-determined. A verifier that has to guess two inputs
reports spurious mismatches, and people then stop trusting the real ones.

The verdicts matter more than the mechanism:

    VERIFIED      reproduced exactly
    DRIFT         config/code moved since; a difference is EXPECTED and is not
                  evidence against the engine
    PARTIAL       differences found, but replay does not yet run every stage
                  the live path runs, so they cannot be attributed
    INSUFFICIENT  the run predates this work and cannot be replayed at all

There is deliberately no MISMATCH verdict. See test_no_premature_mismatch.

INSUFFICIENT is a correct answer, not a failure. Every pre-2026-08-03 session
reports it, because those runs were never reproducible.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from replay import replay, _close, _diff_state, _NOT_OWNED_BY_CORE_TICK  # noqa: E402


def _unique(n): return f"{n}-{uuid.uuid4().hex[:8]}"


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            import database as _db
            if getattr(_db, "_pool", None) is not None:
                loop.run_until_complete(_db.close_pool())
        except Exception:
            pass
        loop.close()


# ── 1. Verdicts ────────────────────────────────────────────────────────────

def test_a_session_with_no_provenance_reports_insufficient_not_failure():
    """Every run made before 4.7. The tool must say so plainly rather than
    inventing a verdict or throwing."""
    class _FakeDB:
        async def get_session_info(self, sid): return {"session_id": sid}
        async def fetch_round_history(self, sid): return []
    r = _run(replay("abc", db=_FakeDB()))
    assert r["verdict"] == "INSUFFICIENT"
    assert "predates" in " ".join(r["notes"])


def test_a_missing_session_does_not_raise():
    class _FakeDB:
        async def get_session_info(self, sid): return None
        async def fetch_round_history(self, sid): return []
    r = _run(replay("nope", db=_FakeDB()))
    assert r["verdict"] == "INSUFFICIENT"
    assert "no such session" in " ".join(r["notes"])


def test_a_single_round_run_is_not_replayable():
    """A replay needs a start state and at least one transition."""
    class _FakeDB:
        async def get_session_info(self, sid):
            return {"run_provenance": {"stochastic_seed": "s", "config_fingerprint": "sha256:x"}}
        async def fetch_round_history(self, sid):
            return [{"round_number": 1, "global_state": {}, "business_units": []}]
    r = _run(replay("x", db=_FakeDB()))
    assert r["verdict"] == "INSUFFICIENT"
    assert "at least one transition" in " ".join(r["notes"])


def test_drift_is_never_reported_as_mismatch():
    """THE honesty requirement. If the config moved after the run, blaming the
    engine for the difference is a lie — and it is the lie a naive verifier
    tells every time someone edits a tunable."""
    class _FakeDB:
        async def get_session_info(self, sid):
            return {"run_provenance": {
                "stochastic_seed": "s",
                "config_fingerprint": "sha256:definitely_not_current",
                "code_version": "deadbee"}}
        async def fetch_round_history(self, sid):
            envelope = {"turn": {"dividends_paid": 0.0, "crisis_severity_effective": 0.0,
                                 "imitation_decay_rate": 0.05,
                                 "decision_paradigm": "legacy_abc",
                                 "emergency_credit_used": False}}
            return [
                {"round_number": 1,
                 "global_state": {"corporate_treasury": 1e7, "group_reputation": 50.0,
                                  "synergy_multiplier": 1.0, "cost_of_capital": 0.05},
                 "business_units": [{"bu_id": "pharma", "revenue_base": 1e6, "opex_base": 5e5,
                                     "natural_capital_debt": 0, "social_license_score": 50,
                                     "reputation_score": 50, "governance_risk_score": 0}],
                 "decisions": [{"bu_id": "pharma", "choice_selected": "option_a",
                                "capex_allocated": 1000.0, "metadata": envelope}]},
                {"round_number": 2,
                 "global_state": {"corporate_treasury": -999999.0, "group_reputation": 3.0,
                                  "synergy_multiplier": 9.0, "cost_of_capital": 0.99},
                 "business_units": [{"bu_id": "pharma", "revenue_base": 1.0, "opex_base": 1.0,
                                     "natural_capital_debt": 0, "social_license_score": 1,
                                     "reputation_score": 1, "governance_risk_score": 99}]},
            ]
    r = _run(replay("x", db=_FakeDB()))
    assert r["differences"], "the fixture is rigged to differ; it must be detected"
    assert r["verdict"] == "DRIFT", r["verdict"]
    joined = " ".join(r["notes"])
    assert "not evidence against the engine" in joined
    assert "deadbee" in joined, "the report must say WHICH code version to check out"


# ── 2. Scope is declared, not implied ──────────────────────────────────────

def test_fields_the_core_tick_does_not_own_are_excluded_by_name():
    """Silent exclusions rot. If replay ignores a field, that must be readable
    in one place rather than inferred from a missing assertion."""
    assert "active_event_flags" in _NOT_OWNED_BY_CORE_TICK
    assert "game_over" in _NOT_OWNED_BY_CORE_TICK
    diffs = _diff_state({"active_event_flags": {"a": 1}, "corporate_treasury": 1.0},
                        {"active_event_flags": {"b": 2}, "corporate_treasury": 1.0},
                        label="t")
    # The flags CONTAINER is never diffed as a value. Its unpacked members are
    # reported, but as kind="absent" — "a stage replay does not run produced
    # this" — never as kind="value", which would read as a wrong number.
    assert not any(d["field"] == "active_event_flags" for d in diffs)
    assert all(d["kind"] == "absent" for d in diffs), diffs
    assert not any(d["field"] == "corporate_treasury" for d in diffs), (
        "a field both sides agree on must not be reported at all"
    )


def test_the_scope_is_stated_in_every_report():
    class _FakeDB:
        async def get_session_info(self, sid): return None
        async def fetch_round_history(self, sid): return []
    r = _run(replay("x", db=_FakeDB()))
    assert "core tick" in r["scope"]


# ── 3. Comparison tolerances ───────────────────────────────────────────────

def test_storage_rounding_is_tolerated_but_real_change_is_not():
    """NUMERIC(18,2) round-trips to the cent. A tolerance wider than that would
    hide exactly the small systematic drifts worth catching."""
    assert _close(1000.0, 1000.004)
    assert not _close(1000.0, 1000.02)
    assert not _close(True, 1.0), "bools must not compare equal to numbers"


# ── 4. End to end on a real session ────────────────────────────────────────

def test_replay_runs_against_a_real_session_without_mutating_it():
    """The property that makes it safe to run on a disputed grade: a
    verification tool that can alter what it verifies is not one."""
    import database as db
    out = _run(db.create_session(cohort_name=_unique("REPLAY"), facilitator_id="god_mode"))
    sid = out.get("session_id") or out.get("id")

    before = _run(db.fetch_latest_state(sid))
    r = _run(replay(sid))
    after = _run(db.fetch_latest_state(sid))

    assert r["verdict"] in {"VERIFIED", "INSUFFICIENT", "DRIFT", "PARTIAL"}
    assert before["round_number"] == after["round_number"]
    assert before["global_state"]["corporate_treasury"] == \
           after["global_state"]["corporate_treasury"]


def test_a_fresh_session_carries_provenance_so_replay_can_at_least_try():
    """Ties 4.7 to its consumer: if provenance regressed, replay would silently
    report INSUFFICIENT forever and nobody would notice."""
    import database as db
    out = _run(db.create_session(cohort_name=_unique("REPLAY-prov"), facilitator_id="god_mode"))
    sid = out.get("session_id") or out.get("id")
    r = _run(replay(sid))
    assert r.get("provenance"), "replay saw no provenance on a session created today"
    assert r["provenance"].get("config_fingerprint")


def test_no_premature_mismatch_verdict():
    """Replay covers pre_tick + process_tick; the live path runs more stages.
    Until one pipeline serves both, a difference cannot be blamed on the
    engine — and a verifier that cries wolf on healthy runs gets ignored, which
    costs more than having no verifier at all."""
    src = (_BACKEND_DIR / "replay.py").read_text(encoding="utf-8")
    assert '"MISMATCH"' not in src.split("KNOWN LIMIT")[-1].split('report["verdict"] = "PARTIAL"')[0] \
        or 'report["verdict"] = "MISMATCH"' not in src, (
        "replay emits MISMATCH while it still covers only part of the pipeline"
    )
    assert 'report["verdict"] = "PARTIAL"' in src
