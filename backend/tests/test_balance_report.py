"""Smoke + determinism guard for the W4 balance-report harness.

The full report (scripts/balance_report.py) is a release-time artifact, too
slow for the suite. This pins the three properties it depends on:
the dry-run pipeline is deterministic for a fixed seed ACROSS calls, its
strategy seeds no longer ride on PYTHONHASHSEED, and the R10 terminal
valuation actually reaches the results (the post_tick return used to be
discarded, which silently dropped mr_breakdown from every dry-run report).
"""

from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("USE_MEMORY_DB", "true")

import dry_run  # noqa: E402
import test_universal_math_engine as UME  # noqa: E402


def _one_run():
    bus = UME.BU_COMPOSITION_FACTORIES["DEFAULT_4_BU"]()
    gs = UME.make_global_state(paradigm="legacy_abc")
    return dry_run._run_one(copy.deepcopy(gs), copy.deepcopy(bus), "balanced",
                            seed=424242, end_round=10, paradigm="legacy_abc",
                            ped_overrides={}, difficulty_tier="standard")


def test_terminal_valuation_reaches_the_result():
    out = _one_run()
    t = out["terminal"]
    assert t is not None
    assert t["regenerative_multiple"] > 0
    assert t["mr_breakdown"], "post_tick extra events dropped again — check _run_one's merge"
    assert t["archetype"]


def test_dry_run_is_deterministic_for_a_fixed_seed():
    a, b = _one_run(), _one_run()
    assert a["terminal"] == b["terminal"]
    assert [r["treasury"] for r in a["rounds"]] == [r["treasury"] for r in b["rounds"]]


def test_strategy_seed_offsets_do_not_use_hash():
    # sha-256-derived, hence stable across processes and PYTHONHASHSEED values
    assert dry_run._stable_strategy_offset("balanced") == \
        int(__import__("hashlib").sha256(b"balanced").hexdigest()[:4], 16) % 1000
