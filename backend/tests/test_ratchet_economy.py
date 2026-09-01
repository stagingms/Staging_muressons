"""Ratchet-economy repair (calibration ruling A+B+C, 2026-09-01).

The diagnosis (CALIBRATION_DIAGNOSIS_2026-09-01.md): per-round FLOW penalties
were written into persistent BASE state, so they compounded without bound —
governance cash-conversion drag into revenue_base (engine.py, "FEATURE 11"),
talent braindrain / NCD penalty / micro-strike into opex_base — while OPEX
inflated every round and revenue had no growth mechanism at all. Every real
team and every scripted strategy went bankrupt by R4-R7.

The ruling: penalties stay real for the round they occur (CSF, the waterfall
and every intra-round reader see the penalized flow) but are reversed from the
persisted base at end of tick (A, C); revenue gains inflation pass-through at
a configurable fraction of cost inflation (B).
"""

from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "tests"))
os.environ.setdefault("USE_MEMORY_DB", "true")

from engine import process_tick  # noqa: E402
import test_universal_math_engine as UME  # noqa: E402


def _tick(gs_mut=None, bus_mut=None):
    bus = UME.BU_COMPOSITION_FACTORIES["DEFAULT_4_BU"]()
    gs = UME.make_global_state(paradigm="legacy_abc")
    gs.setdefault("active_event_flags", {})["stochastic_seed"] = "ratchet-test"
    if gs_mut:
        gs_mut(gs)
    if bus_mut:
        bus_mut(bus)
    decisions = UME.make_decisions(bus, paradigm="legacy_abc", choice="option_b")
    result = process_tick(
        current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
        decisions=decisions, dividends_paid=0.0, crisis_severity=0.0,
        imitation_decay_rate=0.05, decision_paradigm="legacy_abc",
        emergency_credit_used=False,
    )
    return gs, bus, result


def _bu(result, bu_id):
    return next(b for b in result["bu_states"] if b["bu_id"] == bu_id)


def _passthrough():
    from config import INFLATION_REVENUE_PASSTHROUGH
    return INFLATION_REVENUE_PASSTHROUGH


# ── A: governance cash-conversion drag is a flow charge, not base erosion ──

def test_cash_conversion_drag_does_not_erode_revenue_base():
    """With gov risk high, the drag must be evented and hit the round's cash,
    but the PERSISTED revenue_base must not carry it into the next round."""
    def hot_gov(bus):
        for b in bus:
            b["governance_risk_score"] = 50.0  # 10% drag while active
    gs, bus, result = _tick(bus_mut=hot_gov)
    ev = result["events"]
    drags = {k: v for k, v in ev.items() if k.startswith("cash_conversion_drag_")}
    assert drags, "gov risk 50 must produce a cash-conversion drag event"
    infl = ev["inflation_index_applied"]
    dso = (ev.get("dso_working_capital") or {}).get("bu_details", {})
    for b0 in bus:
        b1 = _bu(result, b0["bu_id"])
        deferred = float((dso.get(b0["bu_id"]) or {}).get("deferred_amount", 0.0))
        # base evolves by inflation pass-through (B) minus the legitimate DSO
        # timing deferral (returned next round) — NOT by the 10% conversion
        # haircut, which at gov 50 would be visibly larger.
        expected = b0["revenue_base"] * (1 + infl * _passthrough()) - deferred
        assert b1["revenue_base"] > expected * 0.98, (
            f"{b0['bu_id']}: revenue_base {b1['revenue_base']:,.0f} looks "
            f"conversion-eroded (expected ≈{expected:,.0f} after DSO {deferred:,.0f})"
        )


def test_cash_conversion_drag_still_reduces_cash():
    """Same setup, and the drag must still cost real money: treasury ends
    lower than an identical run with clean governance."""
    def hot_gov(bus):
        for b in bus:
            b["governance_risk_score"] = 50.0
    def clean_gov(bus):
        for b in bus:
            b["governance_risk_score"] = 0.0
    _, _, hot = _tick(bus_mut=hot_gov)
    _, _, clean = _tick(bus_mut=clean_gov)
    assert hot["global_state"]["corporate_treasury"] < clean["global_state"]["corporate_treasury"], (
        "flow-ifying the drag must not delete the penalty itself")


# ── C: braindrain and NCD penalties charge the round, not the base ─────────

def test_braindrain_penalty_does_not_compound_opex_base():
    """Control-based: identical runs at rep 40 vs rep 80 must persist the SAME
    software opex_base once the penalty is a flow charge (it fired in one and
    not the other; only the round's cash should differ)."""
    # group reputation is recomputed from the BU table inside the tick, so
    # the control must set per-BU reputation_score, not the global field.
    def low_rep(bus):
        for b in bus:
            b["reputation_score"] = 40.0
    def high_rep(bus):
        for b in bus:
            b["reputation_score"] = 85.0
    _, _, low = _tick(bus_mut=low_rep)
    _, _, high = _tick(bus_mut=high_rep)
    assert low["events"].get("talent_penalty_applied", 1.0) > 1.0, "penalty must still fire"
    lo, hi = _bu(low, "software")["opex_base"], _bu(high, "software")["opex_base"]
    assert lo == pytest.approx(hi, rel=0.02), (
        f"software opex_base persists the braindrain multiplier: rep40 {lo:,.0f} "
        f"vs rep80 {hi:,.0f} (ratio {lo/hi:.3f})")


def test_ncd_opex_penalty_does_not_compound_opex_base():
    """Control-based: heavy NCD vs zero NCD must persist (nearly) the same
    opex_base; the NCD cost of debt still differs, but the OPEX penalty must
    charge the round, not the base."""
    def heavy(bus):
        for b in bus:
            b["natural_capital_debt"] = 4000.0
    def clean(bus):
        for b in bus:
            b["natural_capital_debt"] = 0.0
    _, _, hot = _tick(bus_mut=heavy)
    _, _, cold = _tick(bus_mut=clean)
    pens = {k: v for k, v in hot["events"].items() if k.endswith("_opex_ncd_penalty")}
    if not pens:
        pytest.skip("NCD penalty stage did not fire on this trajectory")
    for b in cold["bu_states"]:
        pen = pens.get(f"{b['bu_id']}_opex_ncd_penalty", 0.0)
        if not pen:
            continue
        hot_opex = _bu(hot, b["bu_id"])["opex_base"]
        assert hot_opex < b["opex_base"] + pen * 0.5, (
            f"{b['bu_id']}: opex_base retains the NCD penalty "
            f"(hot {hot_opex:,.0f} vs clean {b['opex_base']:,.0f} + pen {pen:,.0f})")


# ── B: nominal symmetry — revenue inflates at a fraction of cost inflation ──

def test_revenue_gains_inflation_passthrough():
    """Controlled: identical ticks with pass-through at config default vs
    forced 0 must differ by exactly the pass-through factor (small tolerance
    for downstream recomputation on the slightly different revenue)."""
    import engine as _engine
    gs, bus, on = _tick()
    ev = on["events"]
    infl = ev["inflation_index_applied"]
    q = _passthrough()
    assert 0.0 < q <= 1.0
    assert ev.get("revenue_inflation_applied") == pytest.approx(infl * q, abs=1e-6)
    saved = _engine.INFLATION_REVENUE_PASSTHROUGH
    try:
        _engine.INFLATION_REVENUE_PASSTHROUGH = 0.0
        _, _, off = _tick()
    finally:
        _engine.INFLATION_REVENUE_PASSTHROUGH = saved
    assert off["events"].get("revenue_inflation_applied") == 0.0
    for b0 in bus:
        ratio = _bu(on, b0["bu_id"])["revenue_base"] / _bu(off, b0["bu_id"])["revenue_base"]
        assert ratio == pytest.approx(1.0 + infl * q, rel=0.01), (
            f"{b0['bu_id']}: pass-through ratio {ratio:.4f} vs expected {1 + infl * q:.4f}")


# ── The point of it all: an investing strategy is no longer doomed by R5 ───

def test_pure_b_at_ten_pct_capex_survives_past_r6():
    import dry_run
    dry_run._EXTRA_STRATEGIES["ratchet_pure_B"] = {
        "label": "ratchet_pure_B", "capex_frac": 0.10, "dividends": 0,
        "scorer": "balanced", "choice_map": {r: "option_b" for r in range(1, 11)},
    }
    bus = UME.BU_COMPOSITION_FACTORIES["DEFAULT_4_BU"]()
    gs = UME.make_global_state(paradigm="legacy_abc")
    out = dry_run._run_one(copy.deepcopy(gs), copy.deepcopy(bus), "ratchet_pure_B",
                           seed=424242, end_round=10, paradigm="legacy_abc",
                           ped_overrides={}, difficulty_tier="standard")
    br = out["bankrupt_round"]
    assert br is None or br > 6, (
        f"pure_B @10% capex still goes bankrupt at R{br} — the spiral is not fixed")
