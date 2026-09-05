"""Natural decay is evaluated on each BU's own investment — audit 2026-09-04 F-17 · WP-21.

The natural-decay tier (growth / mild / hold / 4 % decay of SLO and reputation)
was evaluated on the GROUP-AVERAGE investment ratio: a $0 BU grew +3 SLO per
round whenever the team's average cleared 0.30, and a $3M BU decayed whenever it
did not. Every calibration figure (config.py's 241-decision populations) had
been measured per decision. The tier is now the BU's own ratio; under the CFO
austerity clamp it is the BU's own pre-clamp intent.
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("USE_MEMORY_DB", "true")

from bu_profiles import build_bu_states  # noqa: E402
from engine import process_tick  # noqa: E402


def _gs(**flags):
    return {
        "round_number": 3, "corporate_treasury": 80_000_000.0, "group_reputation": 60.0,
        "synergy_multiplier": 0.9, "cost_of_capital": 0.05,
        "active_event_flags": {"stochastic_seed": "wp21-decay", **flags},
        "historical_ebitda": 0, "tco2e_emissions": 0, "green_transition_fund": 0,
        "tipping_point_active": False, "workforce_readiness": 50.0, "momentum_history": [],
        "pending_capex_projects": [], "inflation_index": 0.025,
        "pedagogical_overrides": {"black_swan_events_enabled": False, "decision_timer_enabled": False},
    }


def _tick(gs, bus, ratios, capex):
    decs = [{"bu_id": b["bu_id"], "investment_ratio": ratios[b["bu_id"]], "capex_allocated": capex[b["bu_id"]],
             "choice_selected": "option_b"} for b in bus]
    return process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus), decisions=decs,
                        dividends_paid=0, crisis_severity=0.0, imitation_decay_rate=0.05,
                        decision_paradigm="legacy_abc")


def _slo(out, bu_id):
    return next(b["social_license_score"] for b in out["bu_states"] if b["bu_id"] == bu_id)


def test_a_zero_bu_decays_while_a_three_million_bu_in_the_same_team_grows():
    bus = build_bu_states()
    for b in bus:
        b["social_license_score"] = 60.0
        b["reputation_score"] = 60.0
    # team average ratio = (0.9 + 0.0 + 0.9 + 0.0) / 4 = 0.45 — above the 0.30 growth bar
    ratios = {"pharma": 0.9, "electronics": 0.0, "consumer_goods": 0.9, "software": 0.0}
    capex = {"pharma": 3_000_000, "electronics": 0, "consumer_goods": 3_000_000, "software": 0}
    out = _tick(_gs(), bus, ratios, capex)
    assert _slo(out, "pharma") > 60.0 and _slo(out, "consumer_goods") > 60.0     # growth tier
    assert _slo(out, "electronics") < 60.0 and _slo(out, "software") < 60.0     # decay tier — not the team average
    # and the mirror image: a $3M BU on a neglectful team still grows
    ratios2 = {"pharma": 0.0, "electronics": 0.0, "consumer_goods": 0.0, "software": 0.9}
    capex2 = {"pharma": 0, "electronics": 0, "consumer_goods": 0, "software": 3_000_000}
    out2 = _tick(_gs(), bus, ratios2, capex2)
    assert _slo(out2, "software") > 60.0 and _slo(out2, "pharma") < 60.0


def test_under_the_austerity_clamp_each_bu_keeps_its_own_intent():
    bus = build_bu_states()
    for b in bus:
        b["social_license_score"] = 60.0
    ratios = {"pharma": 0.9, "electronics": 0.0, "consumer_goods": 0.9, "software": 0.0}
    capex = {"pharma": 3_000_000, "electronics": 0, "consumer_goods": 3_000_000, "software": 0}
    out = _tick(_gs(cfo_austerity_active=True), bus, ratios, capex)
    assert out["events"]["_pre_austerity_ratios"] == ratios
    # the clamp zeroed the spend, but the tier reads the BU's own intent: pharma
    # is judged on 0.9 (growth), software on 0.0 (decay) — not the 0.45 average
    assert _slo(out, "pharma") > _slo(out, "software")
    assert _slo(out, "software") < 60.0
