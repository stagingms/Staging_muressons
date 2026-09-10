"""F07 / N5 (AUDIT_Engines_Flow_Classroom50_20260909, P2) — stakeholder fines
have a basis, a sign, and one applicator. Decision D3 (2026-09-10).

Before: `hit = treasury × |pct|; treasury -= hit` in the agent applicator
(autonomous_agents Phase 3), the NPC-cascade block (round_logic), the
black-swan registry and the regulatory sandbox. A team in emergency credit
(treasury −$10M) hit by the regulator's "4% of annual revenue" shutdown order
was CREDITED $0.4M. The narrative named revenue; the code charged treasury.

Now (fine_basis.apply_cash_effects): a revenue fine is charged on ANNUAL
revenue (2 × Σ revenue_base, the WP-23 convention); a treasury percentage on
max(0, treasury); a flat amount as given; a charge never raises the balance.
Investor / journalist events act through cost of capital and reputation only.
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

from fine_basis import annual_revenue, apply_cash_effects  # noqa: E402
import autonomous_agents as aa  # noqa: E402
import systemic_risk_engine as sre  # noqa: E402

# The default four-BU composition: Σ revenue_base = 53.5M per round.
_BUS = [
    {"bu_id": "pharma", "revenue_base": 18_000_000, "opex_base": 12_000_000, "carbon_intensity": 0.5,
     "social_license_score": 70, "governance_risk_score": 20, "natural_capital_debt": 0,
     "staff_burnout_index": 20, "reputation_score": 70},
    {"bu_id": "electronics", "revenue_base": 16_500_000, "opex_base": 11_500_000, "carbon_intensity": 0.5,
     "social_license_score": 70, "governance_risk_score": 20, "natural_capital_debt": 0,
     "staff_burnout_index": 20, "reputation_score": 70},
    {"bu_id": "software", "revenue_base": 10_500_000, "opex_base": 7_500_000, "carbon_intensity": 0.5,
     "social_license_score": 70, "governance_risk_score": 20, "natural_capital_debt": 0,
     "staff_burnout_index": 20, "reputation_score": 70},
    {"bu_id": "logistics", "revenue_base": 8_500_000, "opex_base": 5_500_000, "carbon_intensity": 0.5,
     "social_license_score": 70, "governance_risk_score": 20, "natural_capital_debt": 0,
     "staff_burnout_index": 20, "reputation_score": 70},
]


def test_annual_revenue_is_two_rounds_of_revenue_base():
    assert annual_revenue(_BUS) == 107_000_000.0


@pytest.mark.parametrize("treasury", [-10_000_000.0, 0.0, 50_000_000.0])
def test_a_revenue_fine_is_charged_on_annual_revenue_whatever_the_treasury(treasury):
    gs = {"corporate_treasury": treasury}
    applied = apply_cash_effects({"revenue_pct_fine": 0.04}, gs, _BUS)
    assert applied == {"revenue_pct_fine": 4_280_000.0}
    assert gs["corporate_treasury"] == pytest.approx(treasury - 4_280_000.0)


def test_a_treasury_percentage_never_credits_a_negative_balance():
    gs = {"corporate_treasury": -10_000_000.0}
    applied = apply_cash_effects({"treasury_pct_hit": -0.08}, gs, _BUS)
    assert applied == {}                      # nothing to take from an empty till
    assert gs["corporate_treasury"] == -10_000_000.0
    gs = {"corporate_treasury": 50_000_000.0}
    applied = apply_cash_effects({"treasury_pct_hit": -0.08}, gs, _BUS)
    assert applied == {"treasury_pct_hit": 4_000_000.0}
    assert gs["corporate_treasury"] == 46_000_000.0


def test_a_flat_hit_is_always_a_charge():
    gs = {"corporate_treasury": -1_000_000.0}
    applied = apply_cash_effects({"treasury_flat_hit": -2_000_000}, gs, _BUS)
    assert applied == {"treasury_flat_hit": 2_000_000.0}
    assert gs["corporate_treasury"] == -3_000_000.0


# ── the configs carry D3 ────────────────────────────────────────────────────

def test_no_agent_or_cascade_uses_a_share_of_treasury_any_more():
    for agent_id, profile in aa.AGENT_PROFILES.items():
        effects = profile["triggered_event"]["effects"]
        assert "treasury_pct_hit" not in effects, agent_id
    for npc_id, gates in sre.STAKEHOLDER_REACTION_GATES.items():
        for gate_id, gate in gates.items():
            assert "treasury_pct_hit" not in gate.get("effects", {}), (npc_id, gate_id)


def test_regulator_fine_is_on_revenue_and_investor_journalist_are_cash_free():
    reg = aa.AGENT_PROFILES["the_regulator"]["triggered_event"]["effects"]
    assert reg["revenue_pct_fine"] == 0.04
    inv = aa.AGENT_PROFILES["the_institutional_investor"]["triggered_event"]["effects"]
    assert "revenue_pct_fine" not in inv and inv["cost_of_capital_delta"] == 0.02 and inv["reputation_delta"] == -15
    jou = aa.AGENT_PROFILES["the_journalist"]["triggered_event"]["effects"]
    assert "revenue_pct_fine" not in jou and jou["reputation_delta"] == -20
    enforcement = sre.STAKEHOLDER_REACTION_GATES["regulator"]["enforcement_action"]["effects"]
    assert enforcement["revenue_pct_fine"] == 0.04
    divest = sre.STAKEHOLDER_REACTION_GATES["activist_investor"]["divestment_campaign"]["effects"]
    assert divest["cost_of_capital_delta"] == 0.01 and divest["reputation_delta"] == -8


# ── the agent applicator, end to end ────────────────────────────────────────

def _force_trigger(agent_id: str):
    """An agent state one tick from triggering: tolerance at the floor."""
    state = aa.create_initial_agent_state()
    for a_id, a in state["agents"].items():
        if a_id != agent_id:
            a["triggered_round"] = 0          # parked: "already triggered", skipped
    state["agents"][agent_id]["tolerance"] = 0.0
    return state


def _tick(agent_id: str, treasury: float):
    gs = {"corporate_treasury": treasury, "group_reputation": 60.0, "cost_of_capital": 0.05,
          "active_event_flags": {}}
    bus = copy.deepcopy(_BUS)
    state = _force_trigger(agent_id)
    new_state, diag = aa.process_agent_tick(state, gs, bus, {}, 5)
    assert agent_id in (diag.get("triggered_agents") or [a for a in new_state["agents"]
                                                          if new_state["agents"][a].get("triggered_round") == 5]), diag
    return gs, bus, diag


def test_regulator_shutdown_charges_4pct_of_annual_revenue_even_in_emergency_credit():
    gs, _, diag = _tick("the_regulator", -10_000_000.0)
    assert gs["corporate_treasury"] == pytest.approx(-14_280_000.0)
    assert diag["agent_treasury_hit_the_regulator"] == pytest.approx(4_280_000.0)
    assert diag["agent_treasury_hit_the_regulator_basis"] == {"revenue_pct_fine": 4_280_000.0}


def test_investor_divestment_leaves_the_treasury_alone_and_moves_cost_of_capital():
    gs, _, diag = _tick("the_institutional_investor", -10_000_000.0)
    assert gs["corporate_treasury"] == -10_000_000.0
    assert gs["cost_of_capital"] == pytest.approx(0.07)
    assert gs["group_reputation"] == pytest.approx(45.0)
    assert "agent_treasury_hit_the_institutional_investor" not in diag


def test_journalist_expose_leaves_the_treasury_alone():
    gs, bus, diag = _tick("the_journalist", 12_000_000.0)
    assert gs["corporate_treasury"] == 12_000_000.0
    assert gs["group_reputation"] == pytest.approx(40.0)
    assert all(b["social_license_score"] == 60 for b in bus)
    assert "agent_treasury_hit_the_journalist" not in diag


# ── the other "% of treasury" applicators are clamped ───────────────────────

@pytest.mark.parametrize("event_id", ["sovereign_debt_crisis", "whistleblower_scandal"])
def test_black_swan_percentage_hit_is_never_a_windfall(event_id):
    """Both global events carry a pure '% of treasury' hit (12 % / 8 %). Forced
    onto a team in emergency credit, the hit is 0 — not a credit of 12 %."""
    from black_swan_registry import BLACK_SWAN_EVENTS, evaluate_black_swans
    rng = BLACK_SWAN_EVENTS[event_id]["trigger_conditions"].get("round_range", [1, 10])
    for treasury, expected in ((-5_000_000.0, 0.0), (10_000_000.0, None)):
        gs = {"corporate_treasury": treasury, "group_reputation": 60.0, "cost_of_capital": 0.05,
              "active_event_flags": {"difficulty_tier": "advanced", "stochastic_seed": "seed"}}
        result = evaluate_black_swans(gs, copy.deepcopy(_BUS), rng[0], "advanced", forced_event_id=event_id)
        fired = [ev for ev in result.get("events_triggered", []) if ev.get("event_id") == event_id]
        assert fired, (event_id, result.get("events_checked"))
        hit = fired[0]["impacts_applied"]["treasury_hit"]
        if expected is not None:
            assert hit == expected, (event_id, treasury, hit)
        else:
            assert hit > 0, (event_id, treasury, hit)      # a positive till is still charged


def test_source_pins_every_percentage_applicator_clamps_at_zero():
    root = _BACKEND_DIR
    swans = (root / "black_swan_registry.py").read_text(encoding="utf-8")
    assert 'max(0.0, float(treasury or 0)) * abs(impacts["treasury_pct_hit"])' in swans
    sandbox = (root / "regulatory_sandbox.py").read_text(encoding="utf-8")
    assert sandbox.count("max(0.0, float(gs") >= 2
    rl = (root / "round_logic.py").read_text(encoding="utf-8")
    assert "from fine_basis import apply_cash_effects" in rl
    agents = (root / "autonomous_agents.py").read_text(encoding="utf-8")
    assert "from fine_basis import apply_cash_effects" in agents
    assert "gs.get(\"corporate_treasury\", 0) * abs(effects[\"treasury_pct_hit\"])" not in agents
