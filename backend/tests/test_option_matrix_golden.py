"""Muressons — option-matrix golden oracle (Phase 0 of the flag remediation).

WHAT THIS ADDS THAT THE EXISTING ORACLES DO NOT
    test_financial_golden_trace.py and test_stakeholder_golden_trace.py each
    drive ONE fixed option path. Measured: that path touches 10 of the 30
    (round, option) pairs round_configs declares, and 20 of the 53 distinct
    flags the decision surface can raise. Reviving a flag set by an option the
    single path never takes therefore moves no fixture, and the change ships
    green. This module drives a covering set instead — three uniform paths give
    30/30 pair coverage — and captures the flag surface alongside the money.

WHAT IT PINS
    Per round, per path: the money surface (identical keys to the financial
    oracle, so the two are comparable), a score surface, and the flag set as
    seen through flag_utils.collect_all_flags. Then the terminal numbers.

THREE FIDELITY FINDINGS, MEASURED WHILE BUILDING THIS
    Recorded here rather than in a document because a finding in a document is
    a note and a finding in a test is a ratchet.

    1. The existing oracles omit the router's three-way active_event_flags merge
       (router.py:3322-3325). Without it only the current round's rN_flags list
       survives: 4 flags visible at R10 instead of 17. This harness performs the
       merge, and test_production_flag_merge_is_applied holds it there.

    2. That omission moves money. With the merge, supply_chain_transparency
       persists and feeds calc_esg_adjusted_wacc's nature premium, so
       cost_of_capital diverges from the financial fixture at R6 (0.0503 here
       against 0.0508 there). WACC sets the exit multiple, so this is not a
       cosmetic difference.

    3. The existing oracles pass the RAW active_event_flags dict to calculate_mr.
       The finale passes flag_utils.mr_flags_from. On the legacy path the raw
       reader awards a Resilience Champion premium the team did not earn — it
       cannot see electronics_water_priority inside r8_flags — and withholds the
       Community Champion premium it did earn. M_R 1.25 against 1.23, terminal
       value 13,513,673 higher. test_terminal_mr_diverges_by_reader pins it.

    None of these are fixed here. Fixing them means rebaselining a working
    fixture, which is a reviewed decision and not a test module's to take.

PHASE 3 (2026-09-08) TOOK THAT DECISION FOR FOUR OTHER OMISSIONS
    Phase 0 left pre_tick, the FLAG-3 flags_set attach, the session-config stamps
    and _forward_persistent_flags out of the harness and said so. Phase 3's read
    probe made them load-bearing: a consumer the harness never executes is
    indistinguishable from a consumer that cannot fire, which is the one
    distinction the probe exists to draw. Measured, each omission hid a documented
    consumer — pre_tick is the only reader of electronics_blindspot and
    deferred_audit; without the flags_set attach apply_decision_sentiment moved
    zero stakeholders in all ten rounds, so carbon_deferred, deny_and_deflect and
    quiet_patch (Appendix B: "LIVE (sentiment only)") looked dead.

    The fixtures were rebaselined for it. The delta is attributable rather than
    asserted: drive(production_steps=False) drops exactly those four steps and
    reproduces the Phase 0 fixtures byte for byte on all four original paths, and
    test_harness_reproduces_the_financial_oracle_when_read_its_way still makes its
    claim in that mode. Findings 1-3 above are unchanged; the reader divergence is
    still M_R 1.25 raw against 1.23 production.

    Two consequences were measured and are held as tests below. Server-derived
    crisis severity (F-07: 0 in every round but R4) moved all_c out of insolvency,
    +49M, taking the whole distress cascade with it — so distress_c was added as a
    directed case to keep it covered. And the score surface gained a `sentiment`
    block, because a flag whose only effect is on stakeholder attitudes moved
    nothing this harness recorded.

KNOWN LIMITATION, STATED RATHER THAN IMPLIED
    terminal_snapshot calls calculate_terminal_value(bus, mr) with no WACC, so
    it uses the FIXED exit multiple. Production's finale uses the dynamic Gordon
    multiple (round_logic._stamp_finale_valuation). The existing financial
    oracle has the same shape, which is why the two remain comparable. Closing
    it is named follow-up work, not something this module silently half-does.
    The router's pillar aggregation and paradigms other than legacy_abc are
    likewise out of scope here.

REBASELINE (deliberate, reviewed)
        MURESSONS_REBASELINE_MATRIX=1 pytest tests/test_option_matrix_golden.py
    Commit the JSON diff in the SAME commit as the change that caused it.
"""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import golden_matrix_harness as H  # noqa: E402

_REBASELINE = os.environ.get("MURESSONS_REBASELINE_MATRIX") == "1"

# ── measured, then pinned ───────────────────────────────────────────────────
_EXPECTED_BARE_RANDOM_DRAWS = 0        # the money path is fully seeded (DEEP-4 #15)
# Both counts moved at Phase 3 and every part of the move is accounted for by
# test_oracle_compatibility_mode_drops_exactly_the_named_steps below: the four
# original paths gain 33 flags and lose 6, and NONE of the 39 is a decision flag.
# The gains are pre_tick's five pre_events plus the engine bookkeeping Phase 0
# threw away by discarding post_tick's and run_new_engines' return values (every
# mr_* breakdown marker, the project/started stamps, the WACC and synergy
# markers). The losses are the distress cascade, which left all_c when
# server-derived crisis severity made it solvent and now lives on distress_c.
# The matrix count also grows with the three paths Phase 3 added: 53 -> 94.
#
# 94 -> 93 (Phase 5). `exit_multiple_ci_haircut` left the matrix, and it was
# never a flag: it is a KEY in the adaptation pathway's `special` config
# (ending_pathways.py:172), and round_logic:3082 stamps it as a FLOAT. It was
# visible only because the R10 finale parked its re-run record in the flag
# namespace under a bare key, so collect_all_flags recursed into the config
# blob inside it (flag_utils.FINALE_INPUTS_KEY records the whole finding). The
# record now sits under the private prefix. No other name moved, on any path,
# under either rule set; the graded quantities did not move under 2026.09 at
# all — see docs/verification/phase5_recalibration.md.
_LEGACY_PATH_DISTINCT_FLAGS = 34       # what a single-path oracle can see
_MATRIX_DISTINCT_FLAGS = 93            # what the covering set sees
# The five flags that exist only because pre_tick runs. If pre_tick is ever
# dropped from the driver again these vanish and test_pre_tick_is_driven fails,
# which is the point: the probe's verdicts are only as honest as the sequence.
_PRE_TICK_SIGNATURE_FLAGS = frozenset({
    "electronics_blindspot_triggered", "crisis_severity_doubled",
    "deep_audit_protected", "deferred_audit_penalty",
    "stakeholder_misanalysis_penalty",
})
# The distress cascade, which lived on all_c until server-derived crisis severity
# made that path solvent. distress_c carries it now.
#
# insolvency_warning joined the set with F07 / D3 (2026-09-10): the investor
# and journalist agents and the divestment cascade stopped draining a
# percentage of the till (they act through cost of capital and reputation
# now), so production all_c ends R10 at $37.8M instead of $29.6M and its
# treasury trend no longer projects insolvency within three rounds. The
# reduced mode's all_c still goes to −$33.5M at R9 and warns there — the same
# "all_c is solvent only in production" story as the six flags above.
_DISTRESS_CASCADE_FLAGS = frozenset({
    "survival_mode", "cfo_austerity_active", "dividends_clamped",
    "dividend_ratchet_triggered", "distress_detected", "phase_transition",
    "insolvency_warning",
})
# The reader divergence on legacy_mixed, from tests/golden/financial_trace.json.
_RAW_READER_MR = 1.25
_PRODUCTION_READER_MR = 1.23


# ═══════════════════════════════════════════════════════════════════
#  COVERAGE — the ratchet that gives this module its reason to exist
# ═══════════════════════════════════════════════════════════════════

def test_matrix_covers_every_declared_round_option():
    """Every (round, option) pair in round_configs is exercised by some path.

    This is the ratchet. Adding option_d to any round, or adding round 11, fails
    here until the matrix covers it — which is the only way a golden master can
    keep up with a growing decision surface.
    """
    declared = H.declared_round_options()
    covered = {(r, o) for path in H.PATHS.values() for r, o in path.items()}
    missing = sorted(declared - covered)
    assert not missing, (
        f"{len(missing)} declared (round, option) pairs are exercised by no path: {missing}\n"
        "Add a path to golden_matrix_harness.PATHS that takes them."
    )


def test_the_single_path_oracles_really_do_leave_a_gap():
    """Guards the premise of this module against silently becoming false.

    If someone widens the financial oracle to cover the whole surface, this test
    fails and this module should be reconsidered rather than maintained out of
    habit.
    """
    declared = H.declared_round_options()
    legacy = {(r, o) for r, o in H.PATHS["legacy_mixed"].items()}
    assert len(legacy) < len(declared), (
        "legacy_mixed now covers the whole declared surface; the gap this module "
        "exists to close is gone."
    )


def test_the_matrix_sees_more_flags_than_one_path_can():
    """The coverage claim in the docstring, enforced as a number."""
    legacy: set[str] = set()
    for rec in H.run_path("legacy_mixed")[:-1]:
        legacy |= set(rec["flags"])
    matrix: set[str] = set()
    for name in H.PATHS:
        for rec in H.run_path(name)[:-1]:
            matrix |= set(rec["flags"])
    assert legacy <= matrix, "the matrix should be a superset of the single path"
    assert len(legacy) == _LEGACY_PATH_DISTINCT_FLAGS, (
        f"legacy path flag count moved: {len(legacy)} (was {_LEGACY_PATH_DISTINCT_FLAGS})")
    assert len(matrix) == _MATRIX_DISTINCT_FLAGS, (
        f"matrix flag count moved: {len(matrix)} (was {_MATRIX_DISTINCT_FLAGS}).\n"
        "  MORE  -> a decision now raises a flag it did not; expected if a flag was revived.\n"
        "  FEWER -> a flag stopped being raised. That is a regression unless it was retired."
    )


# ═══════════════════════════════════════════════════════════════════
#  DETERMINISM — a golden master on a non-deterministic engine is worse
#  than none, so prove it rather than assume it
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("path_name", sorted(H.PATHS))
def test_each_path_is_deterministic(path_name):
    assert H.run_path(path_name) == H.run_path(path_name), (
        f"path '{path_name}' is not reproducible across two runs in one process; "
        "the fixture below cannot mean anything until it is."
    )


def test_bare_global_random_draws_stay_pinned():
    """The whole matrix makes zero un-seeded draws. Hold it there.

    Any count above zero means a path now depends on the bare global `random`
    module, which interleaves across concurrent commits and cannot be replayed
    from a cohort seed.
    """
    seen: list[int] = []
    names = ("random", "randint", "uniform", "choice", "sample", "gauss", "shuffle")
    originals = {n: getattr(random, n) for n in names}
    try:
        for name, orig in originals.items():
            def _wrap(o=orig):
                def w(*a, **k):
                    seen.append(1)
                    return o(*a, **k)
                return w
            setattr(random, name, _wrap())
        for path_name in H.PATHS:
            H.run_path(path_name)
    finally:
        for name, orig in originals.items():
            setattr(random, name, orig)

    assert len(seen) == _EXPECTED_BARE_RANDOM_DRAWS, (
        f"bare global random draws across the matrix changed: {len(seen)} "
        f"(was {_EXPECTED_BARE_RANDOM_DRAWS})."
    )


# ═══════════════════════════════════════════════════════════════════
#  THE FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("rules_version", sorted(H.GOLDEN_DIRS))
@pytest.mark.parametrize("path_name", sorted(H.PATHS))
def test_golden_matrix_matches(path_name, rules_version):
    """One fixture set per rule set (Phase 4).

    The baseline set is the compatibility guarantee: a 2026.09 session replays
    bit-identically however many mechanics 2026.10 revives. The 2026.10 set pins
    the revived semantics, so a revival cannot drift either — an unpinned "new
    rules" branch would be exactly the unguarded state this whole exercise is
    about.
    """
    current = H.run_path(path_name, rules_version=rules_version)
    golden = H.load_golden(path_name, rules_version)

    if _REBASELINE or golden is None:
        H.write_golden(path_name, current, rules_version)
        if golden is None and not _REBASELINE:
            pytest.skip(f"baseline for '{path_name}' @ {rules_version} created; "
                        "re-run to assert against it")
        return

    assert current == golden, (
        f"the engine moved for path '{path_name}' under rules {rules_version}.\n"
        f"{H.first_diff(golden, current)}\n\n"
        "If the change was intended, rebaseline with "
        "MURESSONS_REBASELINE_MATRIX=1 and commit the JSON diff in the same commit."
    )


def test_every_path_captures_all_ten_rounds_and_a_terminal():
    for path_name in H.PATHS:
        trace = H.run_path(path_name)
        assert len(trace) == H.N_ROUNDS + 1, f"{path_name}: expected 11 entries, got {len(trace)}"
        assert [t["round"] for t in trace[:-1]] == list(range(1, H.N_ROUNDS + 1))
        assert "terminal" in trace[-1]
        assert "error" not in json.dumps(trace), f"{path_name}: a round raised"


# ═══════════════════════════════════════════════════════════════════
#  PHASE 4 — the rule sets, and what separates them
# ═══════════════════════════════════════════════════════════════════

# Where the two rule sets are allowed to differ. Every entry is a mechanic
# rules.SWITCHES declares; anything else moving between them is a revival
# leaking into a quantity nobody signed up for.
_REVIVAL_SURFACE = {
    "sdg_index",                    # sdg_flag_bonuses_live (report only)
    "score",                        # sct_flag_boosts_live -> supply_chain_transparency
    "bus",                          # hard_engineering_pulse_revert_live -> carbon_intensity
    "global", "flags", "sentiment", "finale",   # everything the two above feed
    "terminal",                     # terminal_snapshot's reconstruction, likewise
    "escalations",                  # which NPC / agent escalations the cascade fires
}


@pytest.mark.parametrize("path_name", sorted(H.PATHS))
def test_the_baseline_rule_set_is_the_compatibility_floor(path_name):
    """2026.09 is not "the old rules" — it is the semantics every session played
    under, and it is what an unversioned session record means. Every revival in
    Phase 4 sits behind a switch that is OFF in it, so this fixture must never
    move for a reason other than an engine change that would have moved it
    before Phase 4 existed."""
    baseline = H.run_path(path_name, rules_version="2026.09")
    golden = H.load_golden(path_name, "2026.09")
    assert golden is not None, f"no baseline fixture for '{path_name}'"
    assert baseline == golden


@pytest.mark.parametrize("path_name", sorted(H.PATHS))
def test_the_revivals_move_something_and_only_the_right_things(path_name):
    """A switch that changes nothing is not a revival, and a switch that changes
    something nobody declared is a leak. Both are failures."""
    import rules as R

    old = H.run_path(path_name, rules_version="2026.09")
    new = H.run_path(path_name, rules_version="2026.10")
    assert len(old) == len(new)

    moved_keys = set()
    for a, b in zip(old, new):
        for key in set(a) | set(b):
            if a.get(key) != b.get(key):
                moved_keys.add(key)

    stray = sorted(moved_keys - _REVIVAL_SURFACE)
    assert not stray, (
        f"turning the revivals on moved {stray} on path '{path_name}', and no "
        f"switch in rules.SWITCHES claims to touch it:\n"
        + "\n".join(f"  {n}: {s.effect}" for n, s in sorted(R.SWITCHES.items())))

    # …and at least one path must actually move, or the switches are inert.
    assert R.RULE_SETS["2026.10"].switches, "2026.10 declares no switches"


def test_the_cascade_changes_which_escalation_fires_not_just_what_it_costs():
    """The gap the escalations block closes.

    The transparency revival's downstream effect is not only financial. Measured
    on all_c at R6: the baseline takes an NPC enforcement fine and leaves the
    community leader `watchful`; the revived rules take an autonomous-agent event
    and push the community leader to `protest` and three agents to `triggered`.
    That is a different classroom, and until the identities were recorded a change
    swapping one escalation for another of similar cost would have moved no
    fixture at all.
    """
    old = H.run_path("all_c", rules_version="2026.09")
    new = H.run_path("all_c", rules_version="2026.10")
    old_r6, new_r6 = old[5]["escalations"], new[5]["escalations"]

    assert old_r6 != new_r6, (
        "the escalation surface no longer diverges between the rule sets; either "
        "the cascade changed or this block stopped recording identities")
    assert old_r6["npc"] != new_r6["npc"] or old_r6["agents"] != new_r6["agents"], (
        "only the money differs now — the identities are the point of this block")
    # Identifiers only. If narrative text ever leaks in, every copy edit churns
    # seven fixtures and the block stops being usable as a ratchet.
    for record in H.run_path("all_a")[0]["escalations"]["npc"]:
        assert " " not in record, f"narrative text in an escalation id: {record!r}"


def test_at_least_one_path_moves_under_the_revived_rules():
    """Guards the premise of the test above. If every path came out identical the
    stray-key check would pass vacuously and the fixtures would prove nothing."""
    moved = [name for name in H.PATHS
             if H.run_path(name, rules_version="2026.09")
             != H.run_path(name, rules_version="2026.10")]
    assert moved, (
        "no path in the matrix changes when every revival is switched on. Either "
        "the switches are not reaching the engine, or the covering array no "
        "longer raises the flags they read.")


def test_the_supply_chain_response_reaches_the_money():
    """The one revival with a graded blast radius, held as a number.

    Transparency is the transparency term of the nature premium in
    calc_esg_adjusted_wacc (engine.py:3692-3696), which sets the cost of capital,
    which sets the Gordon exit multiple, which multiplies terminal value. If this
    stops being true, rules.SWITCHES["sct_flag_boosts_live"].blast_radius is
    wrong and Phase 5 would recalibrate against a fiction.
    """
    old = H.run_path("all_a", rules_version="2026.09")
    new = H.run_path("all_a", rules_version="2026.10")
    old_sct = [r["score"]["supply_chain_transparency"] for r in old[:-1]]
    new_sct = [r["score"]["supply_chain_transparency"] for r in new[:-1]]
    assert old_sct != new_sct, "the transparency response is not firing"

    # UPDATED AT PHASE 5. This used to assert that all_a FLOORS at 0 — which it
    # did, and which was the measurement that justified recalibrating rather than
    # shipping the revival as it stood. Phase 5 applied each boost once instead of
    # every round and moved the entropy knob, and the floor is gone: measured
    # across 3,300 sampled games the share of runs ending pinned at a clamp fell
    # from 66.9% to 5.1%. The assertion is inverted deliberately, because the old
    # one now describes a state the recalibration exists to have removed.
    assert 0.0 < new_sct[-1] < 100.0, (
        f"all_a ends clamped under the recalibrated rules: {new_sct}. Phase 5's "
        "whole claim is that transparency became a score with a usable middle; if "
        "this path is pinned again, re-run the sweep before trusting anything "
        "derived from it.")
    assert new_sct != old_sct and min(new_sct) < min(old_sct), (
        "the negative flags no longer bite: all_a takes supply_chain_disruption_risk "
        "at R3 and should dip below the baseline's monotone drift")
    assert old[-1]["finale"]["terminal_value"] != new[-1]["finale"]["terminal_value"], (
        "transparency no longer reaches terminal value; the blast radius recorded "
        "in rules.SWITCHES is stale")


# ═══════════════════════════════════════════════════════════════════
#  FIDELITY — the three findings, held as ratchets
# ═══════════════════════════════════════════════════════════════════

def test_production_flag_merge_is_applied():
    """router.py:3322-3325 keeps every round's flag list alive to the finale.

    Drop the merge from the harness and only r10_flags survives, which is the
    state the existing oracles pin and production never produces.
    """
    gs, _ = H.final_state("legacy_mixed")
    aef = gs.get("active_event_flags") or {}
    present = {k for k in aef if k.startswith("r") and k.endswith("_flags")}
    expected = {f"r{n}_flags" for n in range(1, H.N_ROUNDS + 1)}
    assert expected <= present, (
        f"the router's flag merge is not being applied: missing {sorted(expected - present)}")


def test_harness_reproduces_the_financial_oracle_when_read_its_way():
    """Fidelity: this harness is the existing driver plus a NAMED set of steps,
    not a different engine.

    Run the legacy path in oracle-compatibility mode — the four Phase 3 production
    steps off, crisis severity flat at the oracle's 20.0 — read the terminal the
    way the financial oracle reads it (the raw active_event_flags dict), and the
    graded numbers come out identical to tests/golden/financial_trace.json. That
    is what licenses everything else in this module, and running it in the reduced
    mode is what makes the licence auditable: the whole fixture delta belongs to
    steps this module can name, not to an engine that drifted.
    """
    fin_path = H.GOLDEN_DIR.parent / "financial_trace.json"
    if not fin_path.exists():
        pytest.skip("financial_trace.json not present")
    fixture_terminal = json.loads(fin_path.read_text(encoding="utf-8"))[-1]["terminal"]

    gs, bus = H.final_state("legacy_mixed", production_steps=False)
    raw = H.terminal_snapshot(gs, bus, production_path=False)

    assert raw["m_r"] == fixture_terminal["m_r"]
    assert raw["terminal_valuation"] == fixture_terminal["terminal_valuation"]
    assert raw["archetype"] == fixture_terminal["archetype"]


# ═══════════════════════════════════════════════════════════════════
#  THE PHASE 3 PRODUCTION STEPS — each held by the signature it leaves
#  behind, so dropping one fails here rather than silently making the
#  reachability probe blind
# ═══════════════════════════════════════════════════════════════════

def test_pre_tick_is_driven():
    """round_logic._pre_r4_contagion is the ONLY reader of electronics_blindspot
    and deferred_audit. Without pre_tick both flags are unreachable by
    construction and tests/test_flag_reachability.py would report two of
    Appendix B's LIVE flags dead."""
    seen: set[str] = set()
    for name in H.PATHS:
        for rec in H.run_path(name)[:-1]:
            seen |= set(rec["flags"])
    missing = sorted(_PRE_TICK_SIGNATURE_FLAGS - seen)
    assert not missing, (
        f"pre_tick is not being driven: {missing} appear nowhere in the matrix.\n"
        "These are pre_events (router.py:3036) and they are the observable proof "
        "that R1's audit choice reaches R4's crisis severity."
    )


def test_pre_tick_actually_moves_the_r4_crisis():
    """The mechanic behind the signature, not just its trace: R1 option_a
    (electronics_blindspot) must double R4 severity, R1 option_c
    (deferred_audit) must raise it 50%, and R1 option_b must do neither."""
    a = {f for rec in H.run_path("all_a")[:-1] for f in rec["flags"]}
    b = {f for rec in H.run_path("all_b")[:-1] for f in rec["flags"]}
    c = {f for rec in H.run_path("all_c")[:-1] for f in rec["flags"]}
    assert "electronics_blindspot_triggered" in a and "crisis_severity_doubled" in a
    assert "deferred_audit_penalty" in c
    assert "deep_audit_protected" in b
    assert "electronics_blindspot_triggered" not in b | c
    assert "deferred_audit_penalty" not in a | b


def test_the_option_flags_reach_the_sentiment_map():
    """router.py:2946-2960 (FLAG-3). Without the attach, the 58-rule sentiment
    map never receives a decision flag: measured on all_c, zero stakeholders
    moved in all ten rounds. Appendix B calls carbon_deferred, deny_and_deflect
    and quiet_patch LIVE ON SENTIMENT ALONE, so a harness without this reproduces
    inside the test suite the very bug FLAG-3 fixed in production.
    """
    with_attach = H.run_path("all_c")
    without = H.run_path("all_c", production_steps=False)

    def movement(trace):
        rounds = [r for r in trace if "sentiment" in r]
        moved = 0
        for prev, cur in zip(rounds, rounds[1:]):
            moved += sum(1 for k, v in cur["sentiment"].items()
                         if prev["sentiment"].get(k) != v)
        return moved

    assert movement(without) == 0, (
        "the oracle-compatibility mode is supposed to leave sentiment flat; if it "
        "moves, something other than the flags_set attach is driving it")
    assert movement(with_attach) > 0, (
        "no stakeholder attitude moved across the whole run — the option flags are "
        "not reaching stakeholder_sentiment.apply_decision_sentiment")


def test_session_config_is_stamped_on_the_flags_the_engine_reads():
    """router.py:2963 and :2977-2988. difficulty_tier gates the covenant ratio;
    the _systemic_toggles bag is what systemic_risk_engine.systemic_toggle_on
    reads to decide whether the systemic engines run. A cohort's
    pedagogical_overrides win over the settings default, so black swans must
    still be OFF in the bag."""
    from systemic_risk_engine import SYSTEMIC_TOGGLES_FLAG
    gs, _ = H.final_state("legacy_mixed")
    aef = gs.get("active_event_flags") or {}
    assert aef.get("difficulty_tier") == H.DIFFICULTY_TIER
    bag = aef.get(SYSTEMIC_TOGGLES_FLAG)
    assert isinstance(bag, dict) and bag, "the systemic toggle bag is missing"
    assert bag["black_swan_events_enabled"] is False, (
        "PED_OVERRIDES must win over the settings default, as router.py:2980 has "
        "it — otherwise the matrix silently runs with black swans on")
    assert bag["systemic_risk_enabled"] is True


def test_persistent_flag_keys_match_the_router():
    """PERSISTENT_FLAG_KEYS is a copy of router._PERSISTENT_FLAG_KEYS, taken
    because importing router pulls in FastAPI and the database layer. Read the
    router's tuple out of its source so the copy cannot drift."""
    import ast
    import importlib
    src = (Path(__file__).resolve().parent.parent / "router.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    # The tuple mixes string literals with references to constants imported from
    # small modules (SYSTEMIC_TOGGLES_FLAG, _RULES_FLAG). Resolve those through
    # the aliases router itself declares, rather than by importing router — which
    # would pull in FastAPI and the database layer for one tuple — and rather than
    # duplicating the literals here, which is the drift this test exists to catch.
    aliases: dict[str, tuple[str, str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for a in node.names:
                aliases[a.asname or a.name] = (node.module, a.name)

    def _resolve(element):
        if isinstance(element, ast.Constant):
            return element.value
        if isinstance(element, ast.Name) and element.id in aliases:
            module_name, attr = aliases[element.id]
            return getattr(importlib.import_module(module_name), attr)
        raise AssertionError(
            f"_PERSISTENT_FLAG_KEYS holds an element this test cannot resolve "
            f"({ast.dump(element)[:80]}); teach it or use a literal")

    found = None
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "_PERSISTENT_FLAG_KEYS"):
            found = tuple(_resolve(e) for e in node.value.elts)
            break
    assert found is not None, "router._PERSISTENT_FLAG_KEYS not found"
    assert tuple(H.PERSISTENT_FLAG_KEYS) == found, (
        f"the harness copy has drifted from the router:\n"
        f"  harness: {H.PERSISTENT_FLAG_KEYS}\n  router : {found}")


def test_oracle_compatibility_mode_drops_exactly_the_named_steps():
    """The claim that makes the rebaseline auditable rather than asserted.

    Every flag the production sequence raises and the reduced mode does not must
    be a pre_tick pre_event, and nothing in the reduced mode may be absent from
    production except the distress cascade all_c lost when it became solvent.
    """
    def union(production: bool) -> set[str]:
        out: set[str] = set()
        for name in ("all_a", "all_b", "all_c", "legacy_mixed"):
            for rec in H.run_path(name, production_steps=production)[:-1]:
                out |= set(rec["flags"])
        return out

    gained = union(True) - union(False)
    lost = union(False) - union(True)
    declared = {f for r in range(1, H.N_ROUNDS + 1)
                for opt in (H.get_round_config(r).get("options") or {}).values()
                for f in (opt.get("flags_set") or [])}

    assert set(_PRE_TICK_SIGNATURE_FLAGS) <= gained, (
        f"pre_tick's signature is missing from the production run: "
        f"{sorted(set(_PRE_TICK_SIGNATURE_FLAGS) - gained)}")
    # The load-bearing claim. The four steps are plumbing — they run pre_tick,
    # carry session config, attach the option's flags to the decision and stop
    # discarding what post_tick and run_new_engines return. None of them may
    # change which DECISION flags a path raises; if one did, the covering array
    # would no longer mean what its name says and every reachability verdict
    # built on it would be suspect.
    assert not (gained & declared), (
        f"a production step raised a decision flag the reduced mode does not: "
        f"{sorted(gained & declared)} — the covering array's decision semantics moved")
    assert not (lost & declared), (
        f"a production step suppressed a decision flag: {sorted(lost & declared)}")
    assert lost == set(_DISTRESS_CASCADE_FLAGS), (
        f"the production steps lost flags other than the distress cascade: "
        f"{sorted(lost - _DISTRESS_CASCADE_FLAGS)}")


def test_the_distress_cascade_stays_covered():
    """Server-derived crisis severity moved all_c from -19,379,984 to +29,611,117
    and the six distress flags went with it. distress_c is the directed case that
    keeps them in the fixtures; if it stops reaching distress this fails rather
    than the coverage quietly disappearing."""
    seen: set[str] = set()
    for rec in H.run_path("distress_c")[:-1]:
        seen |= set(rec["flags"])
    missing = sorted(_DISTRESS_CASCADE_FLAGS - seen)
    assert not missing, f"distress_c no longer reaches distress: missing {missing}"
    assert H.SPEND["distress_c"]["capex"]["pharma"] == 1_000_000, (
        "distress_c's spend profile is the one the financial oracle's calibration "
        "note measured as insolvent by round 4; changing it needs a new measurement")


def test_terminal_mr_diverges_by_reader():
    """The reader bug, pinned as a number so it cannot be forgotten.

    The raw dict cannot see option flags — they live inside rN_flags lists — so
    on the legacy path it awards Resilience Champion (a three-flag NEGATIVE
    conjunction that electronics_water_priority should have blocked) and misses
    Community Champion (community_fund, set at R9).

    When the existing financial oracle is rebaselined onto mr_flags_from this
    test fails, and that failure is the signal to delete it.
    """
    gs, bus = H.final_state("legacy_mixed")
    raw = H.terminal_snapshot(gs, bus, production_path=False)
    prod = H.terminal_snapshot(gs, bus, production_path=True)

    assert raw["m_r"] == _RAW_READER_MR
    assert prod["m_r"] == _PRODUCTION_READER_MR
    assert prod["m_r"] < raw["m_r"], "the divergence changed direction"

    assert any("Resilience Champion" in b for b in raw["bonuses_earned"]), \
        "the raw reader no longer awards the unearned Resilience Champion premium"
    assert not any("Resilience Champion" in b for b in prod["bonuses_earned"]), \
        "the production reader should be blocked by electronics_water_priority"
    assert any("Community Champion" in b for b in prod["bonuses_earned"]), \
        "the production reader should see community_fund from R9"
