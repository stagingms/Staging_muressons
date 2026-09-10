"""N1 (EVAL_AuditResponse 2026-09-10, action 5) — the BRSR paradigm can be
played from the real client.

The cockpit treats brsr_ngrbc as pillar mode: it fetches
/pillar-config/{n}?paradigm=brsr_ngrbc and commits choice_selected '' plus
pillar_decisions. Before: the endpoint ignored the parameter (every BRSR
player saw the generic Energy / Operations tiles), and the commit path
aggregated pillars for multi_toggles only, so '' reached process_brsr_round
— no BRSR flags, no dimension deltas, an empty history row — while the
suite stayed green because every BRSR test posted option_a straight to the
API. The BRSR pillar config, aggregator and legacy translator existed in
side_tracks/brsr_ngrbc/configs.py and had no caller.

Now the endpoint serves the BRSR areas, the commit aggregates BRSR pillars
and translates them to the A/B/C option the track reads, the events are
labelled brsr_ngrbc, and — as in multi_toggles — the router's aggregates
are the single source of the round's generic impacts (the translated
proxy's cost / reputation / governance do not apply on top; its BRSR
dimension scores do).
"""
import os
os.environ["USE_MEMORY_DB"] = "true"

import pytest
from fastapi.testclient import TestClient
from main import app
from router import _commit_timestamps
from side_tracks.brsr_ngrbc.configs import BRSR_PILLAR_OPTIONS, BRSR_ROUND_CONFIGS

client = TestClient(app)


def _solo(paradigm, name):
    import admin_shared
    admin_shared._god_mode_settings["solo_mode_enabled"] = True
    resp = client.post("/api/simulations/solo-start", json={"player_name": name, "decision_paradigm": paradigm})
    assert resp.status_code == 201, resp.text
    return resp.json()["session_id"]


def _brsr_pillars(rnd: int, pick: int = 0) -> dict:
    """The client's shape: one option per BRSR area, from the BRSR config."""
    out = {}
    for area, spec in BRSR_PILLAR_OPTIONS[rnd]["areas"].items():
        options = list(spec["options"])
        out[area] = options[min(pick, len(options) - 1)]
    return out


def _client_commit(sid, rnd, bus, pillars, expect=201):
    """Exactly what page.js sends in pillar mode: choice_selected '' + pillar_decisions."""
    _commit_timestamps.pop(sid, None)
    r = client.post(f"/api/simulations/{sid}/commit-turn", json={
        "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.2, "capex_allocated": 1_000_000.0,
                       "choice_selected": "", "pillar_decisions": pillars} for b in bus],
        "dividends_paid": 0.0, "force_override_cfo": True, "expected_round": rnd})
    assert r.status_code == expect, f"R{rnd}: {r.status_code} {r.text[:300]}"
    return r.json()


def _all_brsr_pillar_flags(rnd: int) -> set:
    return {f for a in BRSR_PILLAR_OPTIONS[rnd]["areas"].values()
            for o in a["options"].values() for f in o.get("flags_set", [])}


# ── the config the cockpit fetches ──────────────────────────────────────────

def test_pillar_config_serves_the_brsr_areas_when_asked_for_them():
    brsr = client.get("/api/simulations/pillar-config/1?paradigm=brsr_ngrbc")
    assert brsr.status_code == 200, brsr.text[:200]
    body = brsr.json()
    assert body["paradigm"] == "brsr_ngrbc"
    assert body["areas"]["energy"]["label"] == "Board ESG Governance"
    assert "board_esg_committee" in body["areas"]["energy"]["options"]
    assert body["title"] == BRSR_PILLAR_OPTIONS[1]["title"]

    generic = client.get("/api/simulations/pillar-config/1").json()
    assert generic["paradigm"] == "multi_toggles"
    assert generic["areas"]["energy"]["label"] != "Board ESG Governance"
    assert set(generic["areas"]) == set(body["areas"]), "the five area slots are shared; the content is not"

    assert client.get("/api/simulations/pillar-config/1?paradigm=healthcare").status_code == 400
    assert client.get("/api/simulations/pillar-config/11?paradigm=brsr_ngrbc").status_code == 404


# ── a BRSR game through the client's payload shape ──────────────────────────

def test_a_brsr_cohort_played_through_the_client_shape_plays_the_brsr_track():
    sid = _solo("brsr_ngrbc", "BRSR-client")
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    ev1 = None
    for rnd in range(1, 11):
        data = _client_commit(sid, rnd, bus, _brsr_pillars(rnd, pick=0))
        ev = data["events"]
        bus = data.get("business_units") or bus
        assert not (ev.get("engine_failures") or []), ev.get("engine_failures")
        assert ev["decision_paradigm"] == "brsr_ngrbc", (rnd, ev["decision_paradigm"])
        assert ev.get("pillar_cost_applied") is not None, rnd
        assert set(ev["pillar_selections"]) == set(BRSR_PILLAR_OPTIONS[rnd]["areas"]), rnd
        assert ev["pillar_flags"] and set(ev["pillar_flags"]) <= _all_brsr_pillar_flags(rnd), rnd
        processed = ev.get("brsr_round_processed")
        assert processed and processed["choice"] in ("option_a", "option_b", "option_c"), (rnd, processed)
        assert processed["dimension_scores"], rnd
        if rnd == 1:
            ev1 = ev
    flags = client.get(f"/api/simulations/{sid}/dashboard").json()["global_state"]["active_event_flags"]
    assert set(flags["r1_pillar_flags"]) == set(ev1["pillar_flags"])
    assert flags["r1_pillar_flags"] and set(flags["r1_pillar_flags"]) <= _all_brsr_pillar_flags(1)
    track = flags["_brsr_track_state"]
    assert set(track["round_choices"]) == set(range(1, 11)) or set(map(int, track["round_choices"])) == set(range(1, 11))
    assert flags.get("brsr_track_completed") is True
    for k in ("terminal_value", "regenerative_multiple", "profile", "brsr_performance_score"):
        assert k in flags, k


def test_the_pillar_cost_is_charged_once_and_the_proxy_option_does_not_stack():
    """R1, first option of every area: the pillar costs (−$2.5M board
    committee, −$1.5M lobbying register, …) are charged by the router, and
    the translated option_a's own `treasury` impact (BRSR_ROUND_CONFIGS) is
    NOT charged on top; its reputation / governance impacts are not stacked
    either. The proxy's BRSR dimension scores still land."""
    sid = _solo("brsr_ngrbc", "BRSR-once")
    d0 = client.get(f"/api/simulations/{sid}/dashboard").json()
    bus = d0["business_units"]
    pillars = _brsr_pillars(1, pick=0)
    agg_cost = sum(BRSR_PILLAR_OPTIONS[1]["areas"][a]["options"][o]["cost"] for a, o in pillars.items())
    assert agg_cost < 0
    data = _client_commit(sid, 1, bus, pillars)
    ev = data["events"]
    assert ev["pillar_cost_applied"] == agg_cost
    proxy = ev["brsr_round_processed"]["choice"]
    proxy_treasury = BRSR_ROUND_CONFIGS[1]["options"][proxy]["impacts"].get("treasury", 0)
    assert proxy_treasury != 0, "the proxy option carries a cost of its own — the point of the test"
    assert "st_brsr_ngrbc_treasury_r1" not in ev, "the proxy's treasury impact was charged on top of the pillar cost"
    assert "st_brsr_ngrbc_rep_r1" not in ev and "st_brsr_ngrbc_gov_r1" not in ev
    assert ev.get("st_brsr_ngrbc_generic_impacts_pillar_bypass_r1") is True
    # the BRSR dimension scores — the track's own metrics — did land
    assert any(k.startswith("st_brsr_ngrbc_custom_") for k in ev), [k for k in ev if k.startswith("st_brsr")]
    assert ev["brsr_round_processed"]["dimension_scores"]


def test_a_brsr_r10_ending_applies_the_full_option_like_the_main_finale():
    """Round 10 is the finale exception in both pillar paradigms: the router
    skips the aggregates and the translated ending's full impact set applies."""
    sid = _solo("brsr_ngrbc", "BRSR-r10")
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    for rnd in range(1, 10):
        bus = _client_commit(sid, rnd, bus, _brsr_pillars(rnd, pick=1)).get("business_units") or bus
    ev10 = _client_commit(sid, 10, bus, _brsr_pillars(10, pick=0))["events"]
    assert ev10.get("pillar_aggregates_skipped_r10") is True
    assert "st_brsr_ngrbc_generic_impacts_pillar_bypass_r10" not in ev10
    assert ev10["brsr_round_processed"]["choice"] in ("option_a", "option_b", "option_c")


def test_a_brsr_commit_with_neither_pillars_nor_an_option_is_refused():
    """The shape that used to commit '' into the track."""
    sid = _solo("brsr_ngrbc", "BRSR-empty")
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    body = _client_commit(sid, 1, bus, None, expect=400)
    assert body["detail"]["code"] == "brsr_pillars_required"
    assert client.get(f"/api/simulations/{sid}/dashboard").json()["current_round"] == 1


def test_an_explicit_brsr_option_still_commits_without_pillars():
    """The API shape the Force-Advance fallback and the older tests use."""
    sid = _solo("brsr_ngrbc", "BRSR-api")
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    _commit_timestamps.pop(sid, None)
    r = client.post(f"/api/simulations/{sid}/commit-turn", json={
        "decisions": [{"bu_id": b["bu_id"], "investment_ratio": 0.2, "capex_allocated": 1_000_000.0,
                       "choice_selected": "option_b"} for b in bus],
        "dividends_paid": 0.0, "force_override_cfo": True, "expected_round": 1})
    assert r.status_code == 201, r.text[:300]
    ev = r.json()["events"]
    assert ev["decision_paradigm"] == "brsr_ngrbc" and ev.get("pillar_cost_applied") is None
    assert ev["brsr_round_processed"]["choice"] == "option_b"
    assert ev.get("st_brsr_ngrbc_treasury_r1") is not None, "outside pillar mode the option's own cost applies"
