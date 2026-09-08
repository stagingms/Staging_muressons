"""Fog of War — the mechanic that was specified and never implemented.

WHAT WAS WRONG
    engine.py computed `ctx.events["fog_noise"]` every round of the opening
    window and NOTHING read it — not the backend, not the frontend, where the only
    references are a key in a "don't render raw" list and two unrelated tunables.
    So the ±10% uncertainty the feature is named after did not exist, and
    completing the R1 deep forensic audit exempted a team from nothing. The
    exemption test was shape A on top of that: a top-level key read against a
    list-held option flag, false forever.

    Intent was recorded, though, which is why this is an implementation and not an
    invention: `fog_of_war_rounds` and `fog_noise_range` are facilitator tunables
    with per-scenario presets of 1, 3, 4 and 5 rounds, while the engine hardcoded
    2 rounds and ±0.10. Both already carry CFG-08's inert ruling.

THE PROPERTY THAT MAKES THIS SAFE
    The noise is applied at the SERIALISATION boundary (router._bu_out), never to
    stored state. No engine reads a fogged number, no score moves, and the whole
    mechanic needs no recalibration — which is unusual for something this visible
    and is the reason it was built this way. test_the_stored_state_is_never_fogged
    is that property, and it is the one test in this module that must never be
    relaxed.
"""

from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("USE_MEMORY_DB", "true")

import golden_matrix_harness as H   # noqa: E402
import rules as R                   # noqa: E402
from router import _bu_out, _fog_for, _fogged   # noqa: E402

_FOGGED_FIELDS = ("natural_capital_debt", "social_license_score", "governance_risk_score")
_UNFOGGED_FIELDS = ("revenue_base", "opex_base", "reputation_score",
                    "carbon_intensity", "water_dependency", "staff_burnout_index")


def _state(rules_version: str, path: str = "all_a"):
    """A real R1 state from the golden matrix, not a hand-built dict."""
    trace, gs, bus = H.drive(path, rules_version=rules_version)
    return gs, bus


# ═══════════════════════════════════════════════════════════════════
#  THE SAFETY PROPERTY
# ═══════════════════════════════════════════════════════════════════

def test_the_stored_state_is_never_fogged():
    """The property the whole design rests on. Serialising a BU must not touch
    the dict it was serialised from, or the noise would enter the simulation and
    every score would inherit it."""
    _gs, bus = _state("2026.10")
    fog = {"natural_capital_debt_noise": 0.09,
           "social_license_noise": -0.09,
           "governance_risk_noise": 0.05}
    for bu in bus:
        before = copy.deepcopy(bu)
        _bu_out(bu, fog)
        assert bu == before, (
            f"serialising {bu['bu_id']} mutated the stored state — the fog has "
            "leaked out of the display layer and into the simulation")


def test_the_baseline_rule_set_shows_the_truth():
    """2026.09 had no fog in the player's view, because nothing read fog_noise.
    That has to stay exactly true for a session pinned to it."""
    gs, bus = _state("2026.09")
    assert _fog_for(gs) == {}, "the baseline rule set is serving fogged values"
    for bu in bus:
        out = _bu_out(bu, _fog_for(gs).get(bu["bu_id"]))
        for field in _FOGGED_FIELDS:
            assert getattr(out, field) == pytest.approx(bu.get(field, 0)), (
                f"{field} is perturbed under 2026.09")


# ═══════════════════════════════════════════════════════════════════
#  THE MECHANIC
# ═══════════════════════════════════════════════════════════════════

def test_the_revived_rule_set_perturbs_exactly_the_three_named_metrics():
    gs, bus = _state("2026.10")
    # R1 of a path that does NOT take the deep audit, so the fog is on.
    caps: dict = {}

    class _Cap(H.MatrixHooks):
        def on_flags(self, flags, stage, rnd):
            if stage == "merged" and rnd == 1:
                caps["flags"] = dict(flags)
                caps["bus"] = None
            return flags

    trace, gs1, bus1 = H.drive("all_a", hooks=_Cap(), rules_version="2026.10")
    noise = (caps["flags"] or {}).get("fog_noise") or {}
    assert noise, "no fog_noise at R1 — the window is not open"

    moved, untouched = set(), set()
    for bu in bus1:
        per_bu = noise.get(bu["bu_id"])
        if not per_bu:
            continue
        out = _bu_out(bu, per_bu)
        for field in _FOGGED_FIELDS:
            if getattr(out, field) != pytest.approx(bu.get(field, 0)):
                moved.add(field)
        for field in _UNFOGGED_FIELDS:
            if getattr(out, field) != pytest.approx(bu.get(field, 0)):
                untouched.add(field)

    assert moved, "the fog is on and nothing moved"
    assert not untouched, (
        f"the fog perturbed metrics Feature 14 does not name: {sorted(untouched)}")


def test_the_deep_audit_exemption_finally_works():
    """The point of the R1 Deep Forensic Audit. Under 2026.09 the exemption test
    was a top-level key read against a list-held flag, so a team that paid for the
    audit was fogged anyway; under 2026.10 they see the truth from the round after
    they commission it."""
    def fog_rounds(path: str, version: str) -> list[int]:
        seen: list[int] = []

        class _Cap(H.MatrixHooks):
            def on_flags(self, flags, stage, rnd):
                if stage == "merged" and flags.get("fog_of_war_active"):
                    seen.append(rnd)
                return flags

        H.drive(path, hooks=_Cap(), rules_version=version)
        return sorted(seen)

    # all_b takes R1 option_b, the deep audit. all_a takes option_a and does not.
    assert fog_rounds("all_b", "2026.09") == [1, 2], (
        "the baseline is supposed to fog the deep-audit team too — that was the bug")
    assert fog_rounds("all_b", "2026.10") == [1], (
        "a team that commissioned the R1 deep audit should be clear from R2")
    assert fog_rounds("all_a", "2026.10") == [1, 2, 3], (
        "a team that skipped the audit should be fogged for the configured window")


def test_the_window_comes_from_the_facilitator_tunable():
    """fog_of_war_rounds ships at 3 with per-scenario presets of 1, 3, 4 and 5,
    and the engine hardcoded 2. If this stops reading the setting, four scenario
    presets go back to meaning nothing."""
    import admin_shared

    def fog_rounds(version: str) -> list[int]:
        seen: list[int] = []

        class _Cap(H.MatrixHooks):
            def on_flags(self, flags, stage, rnd):
                if stage == "merged" and flags.get("fog_of_war_active"):
                    seen.append(rnd)
                return flags

        H.drive("all_a", hooks=_Cap(), rules_version=version)
        return sorted(seen)

    original = admin_shared._god_mode_settings.get("fog_of_war_rounds")
    try:
        admin_shared._god_mode_settings["fog_of_war_rounds"] = 5
        assert fog_rounds("2026.10") == [1, 2, 3, 4, 5]
        assert fog_rounds("2026.09") == [1, 2], (
            "the baseline must ignore the tunable — it always did")
        admin_shared._god_mode_settings["fog_of_war_rounds"] = 1
        assert fog_rounds("2026.10") == [1]
    finally:
        if original is None:
            admin_shared._god_mode_settings.pop("fog_of_war_rounds", None)
        else:
            admin_shared._god_mode_settings["fog_of_war_rounds"] = original


def test_the_amplitude_comes_from_the_facilitator_tunable():
    import admin_shared

    def sample(version: str):
        caps: dict = {}

        class _Cap(H.MatrixHooks):
            def on_flags(self, flags, stage, rnd):
                if stage == "merged" and rnd == 1 and "fog" not in caps:
                    caps["fog"] = (flags.get("fog_noise") or {})
                return flags

        H.drive("all_a", hooks=_Cap(), rules_version=version)
        values = [abs(v) for per_bu in caps["fog"].values() for v in per_bu.values()]
        return max(values) if values else 0.0

    original = admin_shared._god_mode_settings.get("fog_noise_range")
    try:
        admin_shared._god_mode_settings["fog_noise_range"] = 0.40
        assert sample("2026.10") > 0.10, "the amplitude tunable is not being read"
        assert sample("2026.10") <= 0.40
        assert sample("2026.09") <= 0.10, (
            "the baseline must stay at its hardcoded ±0.10")
    finally:
        if original is None:
            admin_shared._god_mode_settings.pop("fog_noise_range", None)
        else:
            admin_shared._god_mode_settings["fog_noise_range"] = original


# ═══════════════════════════════════════════════════════════════════
#  THE THINGS A FOG MUST NOT DO
# ═══════════════════════════════════════════════════════════════════

def test_the_fog_cannot_be_defeated_by_reading_a_different_endpoint():
    """Every player-facing read goes through _bu_out. If a new endpoint maps BU
    state itself, the fog is one browser tab away from being pointless."""
    import ast
    source = (_BACKEND / "router.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    bare = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "_bu_out" and len(node.args) < 2):
            bare.append(node.lineno)
    assert not bare, (
        f"_bu_out called without a fog argument at line(s) {bare} — that endpoint "
        "serves unfogged values and defeats the mechanic for every other one")


def test_the_scores_stay_in_their_ranges():
    """social_license_score and governance_risk_score are 0-100. A +40% fog on a
    score of 95 must not show 133."""
    assert _fogged(95.0, 0.40, lo=0.0, hi=100.0) == 100.0
    assert _fogged(5.0, -0.90, lo=0.0, hi=100.0) == pytest.approx(0.5)
    assert _fogged(10.0, -3.0, lo=0.0) == 0.0
    assert _fogged(50.0, None) == 50.0, "no noise must mean no change, not zero"
    assert _fogged(None, 0.1) is None
    assert _fogged(True, 0.1) is True, "a bool is not a metric"


def test_the_switch_is_declared_and_off_by_default():
    assert "fog_of_war_display_noise" in R.SWITCHES
    assert R.rule_on({}, "fog_of_war_display_noise") is False
    assert R.rule_on({R.RULES_FLAG: "2026.10"}, "fog_of_war_display_noise") is True
