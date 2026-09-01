"""DEEP-6 + DEEP-7: config-driven greenwash claims; strike docs match the code.

DEEP-6: calc_greenwashing_risk classified EVERY option_a/option_c in EVERY
round as a "green claim" — so Deny & Deflect (R4C), CEO-Only Sign-Off (R2C),
Immediate Closure (R9A) and Divest (R10C) could trigger a *greenwashing*
scandal, with a player-facing message asserting a green claim they never
made. The classification now comes from a per-option `green_claim` config
key ("full" = 15% threshold / -15 SLO, "moderate" = 10% / -7.5, absent =
never checked) — the same config-driven treatment B-4 gave special_rules.

DEEP-7: the student-facing glossary said the R9 strike fires at 75% and
printed a formula that exists nowhere in the code (the config says 50% +
a burnout boost, cap 95%). The glossary entries now interpolate the
configured numbers, so they cannot drift again.
"""

import random

import pytest


# ── DEEP-6 unit level ────────────────────────────────────────────

def test_untagged_option_is_never_a_green_claim():
    from engine import calc_greenwashing_risk
    decs = [{"bu_id": "a", "investment_ratio": 0.0}]
    hit, pen = calc_greenwashing_risk("option_c", decs, claim_level=None)
    assert (hit, pen) == (False, 0.0)


def test_full_claim_checks_at_15pct_full_penalty():
    from engine import calc_greenwashing_risk
    decs = [{"bu_id": "a", "investment_ratio": 0.05}]
    hit, pen = calc_greenwashing_risk("option_b", decs, claim_level="full")
    assert hit is True and pen == 15.0


def test_moderate_claim_checks_at_10pct_half_penalty():
    from engine import calc_greenwashing_risk
    decs = [{"bu_id": "a", "investment_ratio": 0.05}]
    hit, pen = calc_greenwashing_risk("option_a", decs, claim_level="moderate")
    assert hit is True and pen == 7.5
    hit2, _ = calc_greenwashing_risk("option_a",
                                     [{"bu_id": "a", "investment_ratio": 0.12}],
                                     claim_level="moderate")
    assert hit2 is False  # 12% clears the moderate 10% bar


# ── DEEP-6 config resolution ─────────────────────────────────────

def test_green_claim_tags_where_the_story_supports_them():
    from engine import resolve_green_claim
    core_bus = [{"bu_id": "energy"}]
    hc_bus = [{"bu_id": "hospitals"}]
    # Genuine green claims are tagged:
    assert resolve_green_claim(3, "option_c", core_bus, "legacy_abc") == "full"   # Offset & Defer
    assert resolve_green_claim(7, "option_a", core_bus, "legacy_abc") == "full"   # Full Circular
    assert resolve_green_claim(7, "option_c", hc_bus, "legacy_abc") == "full"     # Circular Instrument Hubs
    # The absurd cases are NOT:
    assert resolve_green_claim(4, "option_c", core_bus, "legacy_abc") is None     # Deny & Deflect
    assert resolve_green_claim(2, "option_c", core_bus, "legacy_abc") is None     # CEO-Only Sign-Off
    assert resolve_green_claim(9, "option_a", core_bus, "legacy_abc") is None     # Immediate Closure
    assert resolve_green_claim(10, "option_c", core_bus, "legacy_abc") is None    # Divest
    assert resolve_green_claim(4, "option_a", hc_bus, "legacy_abc") is None       # Deny & Litigate


def test_every_green_claim_value_is_valid():
    from round_configs import get_round_options
    from healthcare_configs import get_healthcare_round_options
    for getter in (get_round_options, get_healthcare_round_options):
        for r in range(1, 11):
            for k, v in (getter(r) or {}).items():
                if isinstance(v, dict) and "green_claim" in v:
                    assert v["green_claim"] in ("full", "moderate"), (r, k, v["green_claim"])


# ── DEEP-6 integration: Deny & Deflect cannot be a greenwash scandal ─

def test_deny_and_deflect_with_thin_capex_is_not_greenwashing():
    import sys
    sys.path.insert(0, "tests")
    from test_r2_materiality_audit import _start, _commit, _submit, Q1_IDS, Q2_IDS, Q3_IDS
    import database_memory as dbm
    random.seed(7)
    sid, bus = _start()
    dbm._global_states[sid][-1].setdefault("active_event_flags", {})[
        "stochastic_seed"] = "greenwash-deep6"
    body = None
    for rnd in range(1, 5):
        if rnd == 2:
            _submit(sid, Q1_IDS, Q2_IDS, Q3_IDS)
        # Thin capex (ratio ~5%) + R4 Deny & Deflect: under the positional
        # heuristic this fired a greenwashing scandal ("your green rhetoric...")
        # for a team that made no green claim at all.
        choice = "option_c" if rnd == 4 else "option_b"
        body = _commit(sid, bus, rnd, choice, capex=500_000)
    ev = body.get("events") or {}
    assert ev.get("greenwashing_scandal") is False, (
        "Deny & Deflect triggered a GREENWASHING scandal: "
        f"{ev.get('greenwashing_message')}")


# ── DEEP-7: the glossary states the code's strike numbers ────────

def _strike_entries():
    from admin_analytics import _glossary_terms
    return [t for t in _glossary_terms
            if "strike" in (t.get("definition", "") + t.get("term", "")).lower()
            or t.get("id") == "social_license"]


def test_glossary_strike_probability_matches_config():
    from round_configs import get_round_config
    pct = int(float((get_round_config(9) or {}).get("special_rules", {})
                    .get("strike_probability_override", 0.50)) * 100)
    entries = _strike_entries()
    assert entries, "glossary strike entries not found"
    joined = " ".join(t.get("definition", "") for t in entries)
    assert "75%" not in joined, "glossary still claims the phantom 75% strike rate"
    assert f"{pct}%" in joined, f"glossary does not state the configured {pct}% base rate"
    assert "(1-SLO/100)" not in joined and "(1−SLO/100)" not in joined, (
        "glossary still prints a strike formula that exists nowhere in the code")
