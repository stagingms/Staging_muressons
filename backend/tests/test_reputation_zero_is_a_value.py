"""Audit F-03 (SEAM-02): a group reputation of 0.0 must be reported as 0, not 50.

The engine clamps reputation at 0 (router.commit_turn board pressure;
round_logic option impacts), so 0.0 is a reachable state — 15 of 20 bot runs
in the audit ended there. admin_debrief_narrative._series_from_history used
`float(gs.get("group_reputation", 50) or 50)`: 0.0 is falsy, the series read 50,
and _turning_point then reported a "+23 up" swing for a team whose reputation
had collapsed. negotiation.apply_concession had the same idiom.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

import admin_debrief_narrative as narrative  # noqa: E402


def _hist(reps):
    return [{"round_number": i + 1,
             "global_state": {"corporate_treasury": 50_000_000, "group_reputation": r, "synergy_multiplier": 1.0}}
            for i, r in enumerate(reps)]


def test_zero_reputation_survives_the_series():
    series = narrative._series_from_history(_hist([50.0, 27.0, 0.0, 0.0]))
    assert [s["reputation"] for s in series] == [50.0, 27.0, 0.0, 0.0]


def test_only_a_missing_reputation_defaults_to_fifty():
    hist = _hist([50.0])
    del hist[0]["global_state"]["group_reputation"]
    assert narrative._series_from_history(hist)[0]["reputation"] == 50.0


def test_a_collapse_to_zero_is_not_reported_as_a_rise():
    series = narrative._series_from_history(_hist([50.0, 27.0, 0.0, 0.0, 0.0]))
    tp = narrative._turning_point(series)
    if tp and tp.get("metric") == "reputation":
        assert tp["direction"] != "up", tp
        assert tp["delta"] <= 0, tp


def test_negotiation_concession_starts_from_zero_not_fifty():
    """public_apology carries reputation_delta -2.0. From 0 the clamp keeps 0;
    the old `or 50` idiom would have produced 48."""
    import negotiation
    agent_id = next(iter(negotiation.AGENT_PROFILES))
    gs = {"group_reputation": 0.0, "corporate_treasury": 10_000_000.0, "active_event_flags": {},
          # a room can only be opened with a hostile, active agent
          "autonomous_agents": {"agents": {agent_id: {"escalation_stage": "hostile", "tolerance": 10}}}}
    opened = negotiation.open_room(gs, [], 3, agent_id)
    assert not opened.get("error"), opened
    res = negotiation.accept_concession(gs, [], 3, "public_apology")
    assert not res.get("error"), res
    assert gs["group_reputation"] == 0.0, gs["group_reputation"]
