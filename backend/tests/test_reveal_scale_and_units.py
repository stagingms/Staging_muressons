"""Reveal scale and units — audit 2026-09-04 F-20 · WP-15.

Share price: 100M shares at a $50 IPO implied a $5.0B market cap against
terminal EVs of $0–0.9B, so every solvent team's reveal read "$1–3 a share,
loss −94%" in red. 6.5M shares = baseline EV ($19.2M seed EBITDA × 17) ÷ $50.

NCD: an index (hard cap 5,000; R10 sums of 47–92 observed) that the reveal
formatted as dollars and the solvency gate subtracted from dollars — inert
both places. The finale now monetises it: points × NCD_OPEX_PENALTY_PER_UNIT
(the engine's per-round OPEX penalty per point) × the finale's exit multiple
— the same capitalisation the EV applies to EBITDA — and publishes both the
points and the dollars for the reveal.
"""
from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO = _BACKEND_DIR.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

from config import TV_SHARES_OUTSTANDING, NCD_OPEX_PENALTY_PER_UNIT  # noqa: E402


def test_share_count_is_on_the_reveal_scale_everywhere():
    assert TV_SHARES_OUTSTANDING == 6_500_000
    cfg = json.loads((_REPO / "simulation_config.json").read_text(encoding="utf-8"))
    assert cfg["terminal_valuation"]["shares_outstanding"] == 6_500_000
    # the volume patcher carries it to production's data volume
    patcher = (_BACKEND_DIR / "patch_volume_config.py").read_text(encoding="utf-8")   # runs at import: read, don't import
    assert '(["terminal_valuation", "shares_outstanding"],' in patcher and "6500000" in patcher
    # the two client-side copies match
    for rel in ("frontend/app/components/stockValuationEngine.js", "frontend/app/components/TerminalValuationCalc.js"):
        src = (_REPO / rel).read_text(encoding="utf-8")
        assert "SHARES_OUTSTANDING = 6_500_000" in src, rel


def _mk_bus(ncd):
    return [{"bu_id": b, "revenue_base": 12_000_000.0, "opex_base": 8_000_000.0,
             "carbon_intensity": 10.0, "social_license_score": 80.0,
             "governance_risk_score": 20.0, "natural_capital_debt": ncd,
             "water_dependency": 30.0, "staff_burnout_index": 10.0,
             "bed_capacity_utilization": 0.5, "talent_penalty": 0}
            for b in ("energy", "electronics", "agri", "software", "pharma")]


def _finale(treasury, ncd):
    from round_logic import post_tick
    random.seed(11)
    bus = _mk_bus(ncd)
    gs = {"corporate_treasury": treasury, "group_reputation": 70.0, "green_transition_fund": 0.0,
          "synergy_multiplier": 1.0, "round_number": 10, "active_event_flags": {},
          "workforce_readiness": 50.0, "climate_resilience": 0.5, "session_id": "", "cost_of_capital": 0.08}
    decs = [{"choice_selected": "option_b", "capex_allocated": 0, "investment_ratio": 0.4, "bu_id": b["bu_id"]} for b in bus]
    extra = post_tick(10, gs, bus, decs, {}, {})
    return gs, bus, extra


def test_finale_publishes_the_monetised_ncd_liability_and_the_points():
    gs, bus, extra = _finale(60_000_000.0, 10.0)
    assert extra["total_ncd_points"] == pytest.approx(sum(b["natural_capital_debt"] for b in bus), abs=0.01)
    expected = extra["total_ncd_points"] * NCD_OPEX_PENALTY_PER_UNIT * extra["exit_multiple"]
    assert extra["ncd_liability_usd"] == pytest.approx(expected, rel=1e-6)
    assert "NCD pts" in extra["ncd_liability_basis"]
    assert extra["dmav"] == pytest.approx(gs["corporate_treasury"] * extra["regenerative_multiple"] - extra["ncd_liability_usd"], abs=1.0)


def test_solvency_gate_reads_the_liability_in_dollars():
    """A modest-treasury team with a catastrophic NCD index is value-destroyed
    once the index is priced; the same team with a small index is not."""
    _, _, ruined = _finale(1_000_000.0, 5_000.0)     # 25,000 pts × $1,000 × multiple ≫ $1M
    assert ruined["ncd_liability_usd"] > ruined["dmav"] and ruined["dmav"] < 0
    assert ruined["profile"] in ("stranded_relic", "hollow_idealist"), ruined["profile"]
    _, _, fine = _finale(60_000_000.0, 10.0)          # 50 pts ≈ $0.6M against $60M
    assert fine["dmav"] > 0
    assert fine["profile"] not in ("stranded_relic", "hollow_idealist"), fine["profile"]


def test_the_index_alone_never_moves_dollars():
    """Source pin: the gate subtracts the liability, not the raw index."""
    import inspect
    import round_logic
    # WP-27: the bridge and the solvency axis live in ONE helper both finales
    # (legacy and BRSR) call — the pin follows the formula.
    src = inspect.getsource(round_logic._equity_and_solvency)
    assert "_dmav = treasury_cash * mr - _ncd_liability" in src
    for fin in (round_logic._stamp_finale_valuation, round_logic._post_brsr_grand_finale):
        assert "_equity_and_solvency(" in inspect.getsource(fin), fin.__name__
