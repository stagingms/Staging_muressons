"""The finale payload carries everything the terminal-valuation waterfall
prints on its M_SDG line — the multiplier the engine USED, the score, the
neutral and the coefficient — so the screen never recomputes it.

Found by the scripted classroom rehearsal (2026-09-10): GameOverSummary
recomputed M_SDG from sdg_impact_score with the 2026.09 arithmetic (neutral
0) and printed "not used this run" plus a caption of M_SDG(1.25×) on a
2026.10 seat whose engine had used 1.0635× (EBITDA $31.4M × 18.0 × 1.77 ×
1.0635 = the $1,064.39M on the same screen). The engine reported
sdg_multiplier already; it now reports sdg_neutral and sdg_coeff too, in
both finale paths, and the product of the four printed factors is the
terminal value.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
sys.path.insert(0, str(_BACKEND_DIR / "tests"))
os.environ.setdefault("USE_MEMORY_DB", "true")

import golden_matrix_harness as H  # noqa: E402
from config import SDG_INDEX_NEUTRAL, SDG_MULTIPLIER_COEFF  # noqa: E402


def _finale(name: str, rules_version: str) -> dict:
    gs, _ = H.final_state(name, rules_version=rules_version)
    return gs["active_event_flags"] or {}


@pytest.mark.parametrize("name", sorted(H.PATHS))
def test_the_four_factors_the_screen_prints_multiply_to_the_terminal_value_2026_10(name):
    f = _finale(name, "2026.10")
    for k in ("sdg_multiplier", "sdg_impact_score", "sdg_neutral", "sdg_coeff",
              "ebitda_used_for_tv", "exit_multiple", "regenerative_multiple", "terminal_value"):
        assert k in f, (name, k)
    assert f["sdg_neutral"] == SDG_INDEX_NEUTRAL and f["sdg_coeff"] == SDG_MULTIPLIER_COEFF
    expected = round(1.0 + ((f["sdg_impact_score"] - f["sdg_neutral"]) / 100.0) * f["sdg_coeff"], 4)
    assert f["sdg_multiplier"] == expected, (name, f["sdg_multiplier"], expected)
    assert f["terminal_value"] == pytest.approx(
        f["ebitda_used_for_tv"] * f["exit_multiple"] * f["regenerative_multiple"] * f["sdg_multiplier"], rel=1e-6), name
    # the arithmetic the screen used to print, for the record: not the product
    if f["sdg_impact_score"] != f["sdg_neutral"]:
        naive = 1.0 + (f["sdg_impact_score"] / 100.0) * 0.25
        assert abs(naive - f["sdg_multiplier"]) > 1e-3, (name, naive)


def test_the_baseline_rule_set_reports_a_neutral_of_zero():
    f = _finale("all_a", "2026.09")
    assert f["sdg_neutral"] == 0 and f["sdg_coeff"] == SDG_MULTIPLIER_COEFF
    assert f["sdg_multiplier"] == 1.0, "no side track on the matrix paths — inert, as the screen says"
