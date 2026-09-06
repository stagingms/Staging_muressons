"""FIN-06 (audit 2026-09-04, Wave 3) — the consequence waterfall is a bridge
from the round's opening treasury to the treasury the round PERSISTS.

Before: `final_treasury` / `entry_count` were struck in the tick's reporting
layer, before the regulatory-ratchet fine (which had no entry at all) and the
post-CSF flow surcharges; then pillar costs, the option's treasury effect, the
cyclone, NPC fines, agent events, cascades, biodiversity, the treasury floor
and the balance sheet's interest moved the treasury by up to $20M a round with
no entry anywhere. The seam probe listed `consequence_waterfall.final_treasury`
apart from every other surface for two waves, and the teleprompter told the
room the waterfall shows EXACTLY how treasury moved.
"""
import copy
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("USE_MEMORY_DB", "true")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bu_profiles import build_bu_states  # noqa: E402
from engine import process_tick  # noqa: E402


def _gs(round_number=1, **flags):
    return {
        "round_number": round_number, "corporate_treasury": 50_000_000.0, "group_reputation": 60.0,
        "synergy_multiplier": 0.35, "cost_of_capital": 0.05,
        "active_event_flags": {"stochastic_seed": "fin06", **flags},
        "historical_ebitda": 0, "tco2e_emissions": 0, "green_transition_fund": 0,
        "tipping_point_active": False, "workforce_readiness": 50.0, "momentum_history": [],
        "pending_capex_projects": [], "inflation_index": 0.025,
        "pedagogical_overrides": {"black_swan_events_enabled": False, "decision_timer_enabled": False},
    }


def _closes(wf, tol=0.05):
    total = wf["initial_treasury"] + sum(e["amount"] for e in wf["entries"])
    return abs(total - wf["final_treasury"]) <= tol


# ── the tick's own waterfall ───────────────────────────────────────────────────

def test_the_ticks_waterfall_closes_on_the_treasury_the_tick_returns_even_with_a_ratchet_fine():
    bus = build_bu_states()
    for b in bus:
        b["governance_risk_score"] = 95.0        # far above the shifting baseline → fine
    gs = _gs(6)
    decisions = [{"bu_id": b["bu_id"], "investment_ratio": 0.05, "capex_allocated": 250_000,
                  "choice_selected": "option_b"} for b in bus]
    out = process_tick(current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus), decisions=decisions,
                       dividends_paid=0, crisis_severity=40.0, imitation_decay_rate=0.05,
                       decision_paradigm="legacy_abc")
    ev, new_gs = out["events"], out["global_state"]
    assert ev["regulatory_ratchet"]["active"] and ev["regulatory_ratchet"]["fine"] > 0
    wf = ev["consequence_waterfall"]
    fine_entries = [e for e in wf["entries"] if e["label"] == "Regulatory ratchet fine"]
    assert len(fine_entries) == 1 and fine_entries[0]["amount"] == pytest.approx(-ev["regulatory_ratchet"]["fine"], abs=0.01)
    assert wf["final_treasury"] == pytest.approx(new_gs["corporate_treasury"], abs=0.01)
    assert wf["entry_count"] == len(wf["entries"])
    assert _closes(wf), (wf["initial_treasury"], wf["final_treasury"], sum(e["amount"] for e in wf["entries"]))
    assert wf["unattributed"] == 0.0


# ── the router's bridge to the persisted treasury ─────────────────────────────

@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from main import app
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    with TestClient(app) as c:
        yield c


def _pillar_decisions(round_number):
    from pillar_configs import get_pillar_config
    cfg = get_pillar_config(round_number) or {}
    return {area: list((spec.get("options") or {}).keys())[0]
            for area, spec in (cfg.get("areas") or {}).items() if spec.get("options")}


def _play(client, paradigm, rounds, capex=1_000_000.0):
    from router import _commit_timestamps
    r = client.post("/api/simulations/solo-start", json={"player_name": "FIN06", "decision_paradigm": paradigm})
    assert r.status_code == 201, r.text[:300]
    sid = r.json()["session_id"]
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    out = []
    for rnd in range(1, rounds + 1):
        _commit_timestamps.pop(sid, None)
        dec = {"investment_ratio": 0.1, "capex_allocated": capex, "choice_selected": "option_a"}
        if paradigm == "multi_toggles":
            dec["pillar_decisions"] = _pillar_decisions(rnd)
        res = client.post(f"/api/simulations/{sid}/commit-turn", json={
            "decisions": [{"bu_id": b["bu_id"], **dec} for b in bus],
            "force_override_cfo": True, "expected_round": rnd, "dividends_paid": 0.0})
        assert res.status_code == 201, f"{paradigm} R{rnd}: {res.text[:300]}"
        body = res.json()
        out.append((rnd, body))
        bus = body.get("business_units") or bus
    return sid, out


from config import VALID_DECISION_PARADIGMS  # noqa: E402


@pytest.mark.parametrize("paradigm", sorted(VALID_DECISION_PARADIGMS))
def test_the_waterfall_closes_on_the_persisted_treasury_every_round(client, paradigm):
    sid, rounds = _play(client, paradigm, rounds=10)
    for rnd, body in rounds:
        wf = body["events"]["consequence_waterfall"]
        stored = body["global_state"]["corporate_treasury"]
        # the response's global_state IS the persisted state (Wave 1 gate: gap 0.00)
        assert wf["final_treasury"] == pytest.approx(stored, abs=0.01), (paradigm, rnd)
        assert wf["entry_count"] == len(wf["entries"])
        assert _closes(wf, tol=0.01 + 0.005 * len(wf["entries"])), (paradigm, rnd, wf["bridge"])
        assert wf["bridge"]["stored"] == pytest.approx(stored, abs=0.01)
        assert wf["bridge"]["closes"] is True
        # the tick's own closing figure is still there for anyone who wants it
        assert "engine_final_treasury" in wf
        # and the tick's own ledger is complete: nothing moved without an entry
        assert wf.get("unattributed", 0.0) == 0.0, (paradigm, rnd, [e["label"] for e in wf["entries"]])
        # no bare residual: every post-tick movement carries a name
        for e in wf["entries"]:
            assert e["label"] and isinstance(e["amount"], (int, float))
    # the dashboard's persisted copy agrees with the response
    dash = client.get(f"/api/simulations/{sid}/dashboard").json()
    last_wf = (dash["global_state"].get("active_event_flags") or {}).get("consequence_waterfall") or {}
    assert last_wf.get("final_treasury") == pytest.approx(dash["global_state"]["corporate_treasury"], abs=0.01)


def test_pillar_costs_and_engine_movements_are_named_entries(client):
    sid, rounds = _play(client, "multi_toggles", rounds=3)
    labels = [e["label"] for _, body in rounds for e in body["events"]["consequence_waterfall"]["entries"]]
    assert "Strategic pillar selections" in labels, labels
    stages = {e.get("stage") for _, body in rounds for e in body["events"]["consequence_waterfall"]["entries"]}
    assert "pillar" in stages
    # a movement inside run_new_engines is attributed to its engine, never to a gap
    assert "Other engine movements" not in labels
    assert "Late adjustments before persistence" not in labels


def test_the_bridge_is_a_pure_function_of_the_stage_figures():
    from waterfall_bridge import bridge_waterfall
    events = {
        "consequence_waterfall": {"initial_treasury": 50.0, "final_treasury": 60.0, "net_change": 10.0,
                                  "entries": [{"label": "Gross Profit (CSF)", "amount": 10.0, "running_total": 60.0}],
                                  "entry_count": 1},
        "ledger_option_treasury": -3.0,
        "climate_event_struck": True, "actual_damage": 2.0,
        "_treasury_moves": [{"engine": "NPC stakeholders (enforcement fines, cascades)", "delta": -4.0},
                            {"engine": "Treasury floor (creditor relief)", "delta": 1.5}],
    }
    wf = bridge_waterfall(events, after_tick=60.0, after_pillar=58.0, after_post_tick=52.5,
                          after_engines=50.0, stored=50.0)
    labels = [e["label"] for e in wf["entries"]]
    assert labels == ["Gross Profit (CSF)", "Strategic pillar selections", "Round option — treasury effect",
                      "Climate event damage", "Other round effects (post-tick)",
                      "NPC stakeholders (enforcement fines, cascades)", "Treasury floor (creditor relief)"]
    amounts = [e["amount"] for e in wf["entries"]]
    assert amounts == [10.0, -2.0, -3.0, -2.0, -0.5, -4.0, 1.5]
    assert wf["final_treasury"] == 50.0 and wf["engine_final_treasury"] == 60.0 and wf["entry_count"] == 7
    assert wf["entries"][-1]["running_total"] == 50.0 and wf["bridge"]["closes"] is True
    # idempotent
    assert bridge_waterfall(events, after_tick=60.0, after_pillar=58.0, after_post_tick=52.5,
                            after_engines=50.0, stored=50.0)["entry_count"] == 7
