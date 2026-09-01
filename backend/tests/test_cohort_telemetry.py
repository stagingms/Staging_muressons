"""Unit tests for the W4.3 cohort-telemetry aggregation (pure functions only —
the data-access layer is exercised manually against the live store)."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("USE_MEMORY_DB", "true")

_spec = importlib.util.spec_from_file_location(
    "_cohort_telemetry", BACKEND.parent / "scripts" / "cohort_telemetry.py")
CT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CT)


def _round(n, treasury, flags=None):
    return {"round_number": n,
            "global_state": {"corporate_treasury": treasury,
                             "active_event_flags": flags or {}},
            "business_units": [], "decisions": []}


def _full_history():
    hist = [_round(n, 50_000_000 - n * 10_000_000,
                   {"greenwashing_scandal": n in (4, 6)}) for n in range(1, 10)]
    hist.append(_round(10, -60_000_000, {
        "terminal_value": 123_000_000.0,
        "regenerative_multiple": 1.25,
        "archetype": "DERISKED_SAFE_HAVEN",
        "mr_breakdown": {"base": 1.0, "resilience_bonus": 0.2,
                         "truth_premium": 0, "wellbeing_bonus": 0.05,
                         "max_achievable_mr": 2.05},
        "black_swan_events": [{"event_id": "x"}],
        "strike_occurred": True,
    }))
    return hist


def test_summarize_team_extracts_the_facts():
    t = CT.summarize_team(_full_history())
    assert t["rounds_played"] == 10
    assert t["terminal_value"] == 123_000_000.0
    assert t["mr"] == 1.25
    assert t["archetype"] == "DERISKED_SAFE_HAVEN"
    # zero-valued and diagnostic keys excluded
    assert t["components"] == ["resilience_bonus", "wellbeing_bonus"]
    assert t["greenwash_rounds"] == 2
    assert t["black_swan_rounds"] == 1
    assert t["bankrupt_round"] == 6  # first negative treasury (R6: 50-60)
    assert t["strike"] is True


def test_lobby_sessions_are_ignored():
    assert CT.summarize_team([]) is None
    assert CT.summarize_team([_round(1, 50_000_000)]) is None


def test_aggregate_cohort_shares_and_zero_rows():
    teams = {"alpha": CT.summarize_team(_full_history()),
             "beta": CT.summarize_team([_round(n, 1_000_000) for n in range(1, 6)])}
    agg = CT.aggregate_cohort(teams)
    assert agg["teams"] == 2 and agg["finished"] == 1
    n, d = agg["component_share"]["resilience_bonus"]
    assert (n, d) == (1, 1)
    n0, _ = agg["component_share"]["synergy_bonus"]
    assert n0 == 0  # never-earned components still get a row (the signal)
    assert agg["bankrupt"] == 1
    assert agg["strike_any"] == 1
