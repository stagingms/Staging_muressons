"""The glossary's load-bearing numbers come from config — and stay there.

W3 (2026-09-01). DEEP-7 fixed the strike entries after the glossary claimed a
75% strike probability and printed a formula that existed nowhere in the code.
The W3 sweep found six more drifted entries (macro rate cycles, M_R range and
synergy bonus, inflation, the turnaround trigger, greenwash mechanics, burnout
drift). The fix is structural: those entries now interpolate the same
constants the engine imports, so a config change updates the glossary.

This test guards the wiring in two directions:
  1. each audited entry must contain the CURRENT config-derived value;
  2. the stale literals that drifted must never reappear anywhere.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("USE_MEMORY_DB", "true")

from admin_analytics import _glossary_terms, _MACRO_TEXT, _STRIKE_PCT  # noqa: E402
from config import (  # noqa: E402
    FINANCIAL_FREE_CSF_PCT, FINANCIAL_DEFAULT_LOAN_RATE,
    OVERRUN_CAPEX_THRESHOLD, OVERRUN_DEFAULT_PROBABILITY,
    DIVIDEND_CUT_THRESHOLD, DIVIDEND_CUT_REP_PENALTY,
    NCD_INTEREST_COEFFICIENT, TECH_DEBT_PENALTY_RATE,
    BRAINDRAIN_REPUTATION_THRESHOLD, CYCLONE_PROB_BASE,
    PHYSICAL_VAR_DAMAGE_BASE, GREENWASH_INVESTMENT_THRESHOLD,
    GREENWASH_SLO_PENALTY,
)
from terminal_valuation import MR_FLOOR, MR_CEILING  # noqa: E402
from engine import _MACRO_RATE_CYCLES  # noqa: E402

_BY_ID = {t["id"]: t["definition"] for t in _glossary_terms}


def _defn(entry_id: str) -> str:
    assert entry_id in _BY_ID, f"glossary entry '{entry_id}' disappeared"
    return _BY_ID[entry_id]


# ── 1. Audited entries carry the current config values ─────────────────────

def test_csf_pool_tracks_config():
    d = _defn("csf_pool")
    assert f"{FINANCIAL_FREE_CSF_PCT * 100:g}%" in d
    assert f"{FINANCIAL_DEFAULT_LOAN_RATE * 100:g}%" in d


def test_capex_tracks_overrun_config():
    d = _defn("capex")
    assert f"${OVERRUN_CAPEX_THRESHOLD / 1e6:g}M" in d
    assert f"{OVERRUN_DEFAULT_PROBABILITY * 100:g}%" in d


def test_cost_of_capital_is_generated_from_the_engine_cycle():
    d = _defn("cost_of_capital")
    assert _MACRO_TEXT in d
    # and the generated text tracks the actual dict
    for pct in {f"{abs(v) * 100:g}" for v in _MACRO_RATE_CYCLES.values() if v}:
        assert pct in _MACRO_TEXT


def test_dividend_ratchet_tracks_config():
    d = _defn("dividend_ratchet")
    assert f"{(1 - DIVIDEND_CUT_THRESHOLD) * 100:g}%" in d
    assert f"-{DIVIDEND_CUT_REP_PENALTY:g}" in d


def test_ncd_coefficient_and_derived_example_agree():
    d = _defn("ncd")
    assert f"{NCD_INTEREST_COEFFICIENT:g}" in d
    assert f"{(0.05 + 5200 * NCD_INTEREST_COEFFICIENT) * 100:g}%" in d


def test_mr_range_is_the_arbiter_clamp():
    d = _defn("mr")
    assert f"[{MR_FLOOR:g}, {MR_CEILING:g}]" in d
    assert "+0.15" in d  # STRAT-010 synergy value, not the pre-fix +0.30


def test_greenwash_entry_tracks_config():
    d = _defn("greenwashing_engine")
    assert f"{GREENWASH_INVESTMENT_THRESHOLD * 100:g}%" in d
    assert f"-{GREENWASH_SLO_PENALTY:g}" in d
    assert "green_claim" in d  # DEEP-6 semantics, not the old R3C heuristic


def test_strike_entries_track_r9_config():
    for eid in ("social_license", "strike_engine"):
        assert f"{_STRIKE_PCT}%" in _defn(eid)


def test_synergy_boost_tracks_r7_config():
    from admin_analytics import _R7C_SYNERGY_BOOST
    from round_configs import get_round_config
    cfg = (get_round_config(7)["options"]["option_c"]["impacts"]
           ["synergy_multiplier_boost"])
    assert _R7C_SYNERGY_BOOST == cfg
    for eid in ("synergy_engine", "synergy_multiplier", "circular_economy"):
        assert f"+{cfg:g}" in _defn(eid)


def test_misc_entries_track_config():
    assert f"{TECH_DEBT_PENALTY_RATE * 100:g}%" in _defn("technical_debt")
    assert f"{BRAINDRAIN_REPUTATION_THRESHOLD:g}" in _defn("brain_drain")
    assert f"{CYCLONE_PROB_BASE * 100:g}%" in _defn("stochastic_climate")
    assert f"${PHYSICAL_VAR_DAMAGE_BASE / 1e6:g}M" in _defn("stochastic_climate")


# ── 2. The stale literals stay dead ────────────────────────────────────────

_STALE = [
    "a loan at 12% interest is auto-triggered",  # CapEx is interest-only (DEEP-8)
    "Below $5M triggers Turnaround Mode",        # turnaround enters at $0 + rep<30
    "range 0.60-2.08",                            # clamp is [0.0, 2.05] (DEEP-2/3)
    "Synergy +0.30,",                             # STRAT-010 reduced it to +0.15
    "+2.5%/round",                                # default inflation is 5%/round
    "R1-3 easing (-0.5%)",                        # engine cycle is R1-2 -1% ...
    "ALL BUs lose 8 SLO points",                  # DEEP-6 config-driven penalties
    "adds +3 drift",                              # natural drift is +6/round
    "+0.35 to synergy",                           # R7C config ships 0.3
    "boosts +0.35",                               # same
]


def test_stale_literals_never_return():
    joined = " || ".join(t["definition"] for t in _glossary_terms)
    for lit in _STALE:
        assert lit not in joined, f"stale figure returned to the glossary: {lit!r}"


# ── 3. The teleprompter carries the same discipline ────────────────────────

_TELEPROMPTER_STALE = [
    "unlocks +0.30 M_R",                 # STRAT-010: synergy bonus is +0.15
    '"value": 0.30, "source": "R7',      # mr_breakdown_guide synergy row
    "Max M_R achievable: 1.98",          # ceilings pinned at 1.93 / 2.02
    "up to 1.98x",                       # pillar ceiling is 2.02
    "EBITDA × 12× × M_R",                # exit multiple is WACC-coupled 6-18x
]


def test_teleprompter_stale_literals_never_return():
    src = (BACKEND / "admin_teleprompter.py").read_text(encoding="utf-8", errors="replace")
    for lit in _TELEPROMPTER_STALE:
        assert lit not in src, f"stale figure returned to the teleprompter: {lit!r}"
