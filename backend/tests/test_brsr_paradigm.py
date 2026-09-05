"""VAL-06 (audit 2026-09-04, WP-27): a brsr_ngrbc session plays the BRSR track.

Before: router.commit_turn never passed decision_paradigm to post_tick, so a
BRSR cohort played the legacy crises with legacy flags and ended on the legacy
finale; /round-config had no BRSR branch; and the first time the BRSR finale
ever ran end-to-end (here) its write-back raised on four unprefixed flags.
This file used to create the session as legacy_abc despite its own comment.

Also pins the paradigm label the router stamps on every commit — it was the
literal "legacy_abc" for every non-pillar paradigm, which is how
advanced_climate paid the legacy mid-game carbon OPEX on top of its own
internal fee.
"""
import os
os.environ["USE_MEMORY_DB"] = "true"

import pytest
from fastapi.testclient import TestClient
from main import app
from router import _commit_timestamps

client = TestClient(app)


def _solo(paradigm, name="Pioneer"):
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    resp = client.post("/api/simulations/solo-start", json={"player_name": name, "decision_paradigm": paradigm})
    assert resp.status_code == 201, resp.text
    return resp.json()["session_id"]


def _commit(sid, rnd, bus, choice="option_a"):
    _commit_timestamps.pop(sid, None)
    r = client.post(f"/api/simulations/{sid}/commit-turn", json={
        "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.2, "capex_allocated": 1_000_000.0,
                       "choice_selected": choice} for b in bus],
        "dividends_paid": 0.0, "force_override_cfo": True, "expected_round": rnd})
    assert r.status_code == 201, f"R{rnd}: {r.text[:300]}"
    return r.json()


def test_brsr_session_plays_the_brsr_track_to_its_own_finale():
    sid = _solo("brsr_ngrbc")
    info = client.get(f"/api/simulations/{sid}/session-info").json()
    assert info["decision_paradigm"] == "brsr_ngrbc"

    # the cockpit is handed the BRSR round, not the legacy one
    rc = client.get(f"/api/simulations/round-config/1?session_id={sid}")
    assert rc.status_code == 200
    assert "BRSR" in rc.json()["crisis"]["title"]
    rc10 = client.get(f"/api/simulations/round-config/10?session_id={sid}").json()
    assert "ending_pathway" not in (rc10.get("special_rules") or {}), "no legacy ending-pathway overlay on the BRSR R10"

    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    ev = None
    for rnd in range(1, 11):
        data = _commit(sid, rnd, bus)
        ev = data["events"]
        bus = data.get("business_units") or bus
        assert ev["decision_paradigm"] == "brsr_ngrbc", rnd
        if rnd == 1:
            assert ev.get("brsr_round_processed"), "R1 ran the BRSR controller"
            assert "electronics_blindspot" not in (ev.get("r1_flags") or []), "not the legacy R1 option flags"
            assert ev.get("midgame_carbon_cost_r1") is None, "the BRSR track has its own carbon accounting"
    # the BRSR finale, with the same bridge the main finale stamps
    flags = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]["active_event_flags"]
    assert flags.get("brsr_track_completed") is True
    assert isinstance(flags.get("brsr_performance_score"), (int, float))
    for k in ("terminal_value", "regenerative_multiple", "profile", "archetype",
              "equity_value", "price_per_share", "net_debt", "final_report_canonical"):
        assert k in flags, k
    assert flags["final_report_canonical"]["terminal_value"] == pytest.approx(flags["terminal_value"], abs=0.01)
    assert flags["price_per_share"] >= 1.0
    # the finale numbers are the CLOSING state's (restamped after the engines):
    fr = client.get(f"/api/simulations/{sid}/final-report").json()
    assert fr["report_access"] == "full"
    assert fr["final_report_canonical"]["terminal_value"] == pytest.approx(flags["terminal_value"], abs=0.01)
    assert flags.get("final_treasury") == pytest.approx(
        client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]["corporate_treasury"], abs=0.01)
    # and the game is over
    _commit_timestamps.pop(sid, None)
    again = client.post(f"/api/simulations/{sid}/commit-turn", json={
        "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.2, "capex_allocated": 1.0,
                       "choice_selected": "option_a"} for b in bus],
        "force_override_cfo": True, "expected_round": 11})
    assert again.status_code in (400, 409), again.text[:200]


@pytest.mark.parametrize("paradigm,expected_label,carbon_opex", [
    ("legacy_abc", "legacy_abc", True),
    ("advanced_climate", "advanced_climate", False),   # its own escalating internal fee
    ("healthcare", "healthcare", True),
])
def test_commit_events_carry_the_real_paradigm_label(paradigm, expected_label, carbon_opex):
    sid = _solo(paradigm, name=f"L-{paradigm[:6]}")
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    ev = _commit(sid, 1, bus)["events"]
    assert ev["decision_paradigm"] == expected_label
    assert (ev.get("midgame_carbon_cost_r1") is not None) is carbon_opex, ev.get("midgame_carbon_cost_r1")
    # and the label persists on the flags the next round's post_tick reads
    flags = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]["active_event_flags"]
    assert flags.get("decision_paradigm") == expected_label


def test_multi_toggles_without_pillar_decisions_still_reads_legacy():
    """The pillar/legacy distinction the label used to carry is preserved."""
    sid = _solo("multi_toggles", name="MT-fallback")
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    ev = _commit(sid, 1, bus)["events"]          # no pillar_decisions → legacy path
    assert ev["decision_paradigm"] == "legacy_abc"
