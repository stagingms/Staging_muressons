"""Muressons — the versioned rule sets (Phase 4 of the dead-flag remediation).

WHAT THIS MODULE IS GUARDING
    Phase 4 turns on mechanics that were designed, written into the engine, and
    never ran. Every one of them changes what a result means, and cohorts are in
    flight with published results. The whole safety argument is one sentence: a
    session pinned to 2026.09 replays bit-identically, whatever is added to
    2026.10. These tests are that sentence, made executable.

    They are deliberately paranoid about the FALLBACK paths rather than the happy
    one, because the failure that would actually hurt is silent: a session record
    with no version, or a version this build does not recognise, quietly picking
    up the newest semantics and re-grading a cohort that has already been
    debriefed.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

import rules as R  # noqa: E402


# ═══════════════════════════════════════════════════════════════════
#  THE COMPATIBILITY GUARANTEE
# ═══════════════════════════════════════════════════════════════════

def test_the_baseline_version_has_every_switch_off():
    """2026.09 is not "the old rules". It is the semantics every existing session
    was played under, and it is what an unversioned record means. If a switch
    ever defaults on here, every past cohort is silently re-graded."""
    baseline = R.RULE_SETS[R.DEFAULT_RULES_VERSION]
    on = sorted(k for k, v in baseline.switches.items() if v)
    assert not on, (
        f"{R.DEFAULT_RULES_VERSION} has {on} switched ON. That version is the "
        "compatibility floor and must stay inert.")


def test_new_sessions_are_created_on_the_revived_rule_set():
    """The Phase 5 cut-over (2026-09-08). Phase 4 wired the mechanics and left
    them off; this line is what turns them on for sessions created from now on.

    It stayed at the baseline until the recalibration was measured and published
    (docs/verification/phase5_recalibration.md). Moving it again is the same kind
    of decision and should fail here until someone updates this test on purpose.
    """
    assert R.CURRENT_VERSION == "2026.10", (
        "CURRENT_VERSION moved. New sessions are graded under it, so it needs a "
        "measured delta report, not a green test.")
    assert R.CURRENT_VERSION in R.RULE_SETS, "new sessions pinned to an unknown rule set"
    assert R.DEFAULT_RULES_VERSION == "2026.09", (
        "DEFAULT_RULES_VERSION is the semantics every already-played session was "
        "graded under. It is a compatibility floor, not a default to modernise.")


def test_the_cut_over_did_not_re_grade_a_single_existing_session():
    """The compatibility guarantee, stated three ways.

    A record stamped with a version keeps it; a record with no stamp — which is
    every session written before Phase 4 — resolves to the baseline and not to
    whatever the current build creates; and neither path consults
    CURRENT_VERSION, so moving it cannot reach an existing game.
    """
    assert R.resolve_version({R.RULES_FLAG: "2026.09"}) == "2026.09"
    assert R.resolve_version({"active_event_flags": {R.RULES_FLAG: "2026.09"}}) == "2026.09"
    assert R.resolve_version({}) == R.DEFAULT_RULES_VERSION == "2026.09"
    assert R.resolve_version({"active_event_flags": {}}) == "2026.09"
    # An unknown pin degrades to the baseline, never to the current version.
    assert R.resolve_version({R.RULES_FLAG: "2027.06"}) == "2026.09"
    # And the router's own fallback is the constant, not the current version.
    router_src = (_BACKEND / "router.py").read_text(encoding="utf-8")
    assert 'get("rules_version") or _DEFAULT_RULES' in router_src, (
        "router.commit_turn no longer falls back to DEFAULT_RULES_VERSION when a "
        "session record carries no rules_version; an unstamped record would now "
        "be re-graded under whatever the build defaults to")


def test_an_existing_session_replays_bit_identically_after_the_cut_over():
    """A session pinned to the baseline must produce the numbers it produced
    before the cut-over — not approximately, exactly. The golden matrix is the
    fixture: seven covering paths, ten rounds, every graded quantity."""
    import json
    sys.path.insert(0, str(_BACKEND / "tests"))
    import golden_matrix_harness as H

    for path_name in H.PATHS:
        golden = json.loads((H.GOLDEN_DIRS["2026.09"] / f"{path_name}.json")
                            .read_text(encoding="utf-8"))
        trace, gs, bus = H.drive(path_name, rules_version="2026.09")
        current = trace + [{"finale": H.finale_snapshot(gs),
                            "terminal": H.terminal_snapshot(gs, bus, production_path=True)}]
        assert current == golden, (
            f"a session pinned to 2026.09 no longer replays as it did, on path "
            f"{path_name}. The cut-over has reached an existing game.")
        # and the switches really are off for that session
        stamped = {R.RULES_FLAG: "2026.09"}
        assert not any(R.rule_on(stamped, name) for name in R.SWITCHES), (
            "a 2026.09-stamped bag reads a revived switch as ON")


def test_every_switch_is_declared_in_every_rule_set():
    """A switch present in one rule set and absent from another would resolve to
    a KeyError at read time, in the middle of a tick, for one cohort."""
    for version, ruleset in R.RULE_SETS.items():
        missing = sorted(set(R.SWITCHES) - set(ruleset.switches))
        extra = sorted(set(ruleset.switches) - set(R.SWITCHES))
        assert not missing, f"{version} does not declare {missing}"
        assert not extra, f"{version} declares undeclared switches {extra}"


def test_every_switch_documents_its_site_shape_effect_and_blast_radius():
    """A switch is a promise about behaviour. A promise with no site and no
    magnitude is an opinion, and Phase 5 has to schedule recalibration from
    exactly this field."""
    for name, switch in R.SWITCHES.items():
        for field in ("site", "shape", "effect", "blast_radius"):
            assert getattr(switch, field).strip(), f"{name} has no {field}"
        assert name == switch.name, f"{name} is keyed under the wrong name"


# ═══════════════════════════════════════════════════════════════════
#  RESOLUTION — the paths that decide which semantics a session gets
# ═══════════════════════════════════════════════════════════════════

def test_an_unversioned_state_is_the_baseline():
    """Every session record written before Phase 4 has no rules_version. This is
    the case that covers all of them."""
    assert R.resolve_version({}) == R.DEFAULT_RULES_VERSION
    assert R.resolve_version({"active_event_flags": {}}) == R.DEFAULT_RULES_VERSION
    assert R.resolve_version(None) == R.DEFAULT_RULES_VERSION


def test_the_version_is_read_from_a_global_state_or_a_bare_flag_dict():
    """calc_supply_chain_transparency receives `flags`, not `gs`. A reader that
    only understood one shape would force every consumer to be re-plumbed, which
    is how the original defect got its foothold."""
    assert R.resolve_version({"active_event_flags": {R.RULES_FLAG: "2026.10"}}) == "2026.10"
    assert R.resolve_version({R.RULES_FLAG: "2026.10"}) == "2026.10"


def test_pedagogical_overrides_carry_the_version_for_direct_callers():
    """The golden harnesses and dry_run.py have no router to stamp for them —
    the same accommodation systemic_toggle_on makes, for the same reason."""
    assert R.resolve_version({"pedagogical_overrides": {"rules_version": "2026.10"}}) == "2026.10"


def test_the_stamped_flag_beats_the_override():
    """The router stamps from the session record every commit. That is the
    authority; an override is a fallback for callers that have none."""
    state = {
        "active_event_flags": {R.RULES_FLAG: "2026.09"},
        "pedagogical_overrides": {"rules_version": "2026.10"},
    }
    assert R.resolve_version(state) == "2026.09"


def test_an_unknown_version_degrades_to_the_baseline_and_says_so():
    """THE IMPORTANT ONE. A session pinned to a version this build does not know
    — a typo, or a record written by a newer build and replayed by an older one —
    must not be re-graded under whatever this build thinks is newest. It also
    must not raise: a classroom is sitting in front of it."""
    # A local handler rather than caplog, so the assertion survives a run with
    # the logging plugin disabled — which is how the flag suite is run.
    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = _Capture()
    logger = logging.getLogger("rules")
    logger.addHandler(handler)
    previous = logger.level
    logger.setLevel(logging.WARNING)
    try:
        assert R.resolve_version({R.RULES_FLAG: "2027.06"}) == R.DEFAULT_RULES_VERSION
        assert R.rule_on({R.RULES_FLAG: "2027.06"}, "sct_flag_boosts_live") is False
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous)

    assert any("unknown rules_version" in r.getMessage() for r in records), (
        "an unrecognised version was swallowed silently; it has to be visible in "
        "the log or nobody will ever find out a cohort played the wrong rules")


def test_a_newer_version_never_leaks_into_an_older_session():
    """The property the whole phase rests on, stated directly."""
    old = {"active_event_flags": {R.RULES_FLAG: "2026.09"}}
    for switch in R.SWITCHES:
        assert R.rule_on(old, switch) is False, (
            f"{switch} is live for a 2026.09 session — every past cohort just got "
            "re-graded")


# ═══════════════════════════════════════════════════════════════════
#  THE TYPO GUARD
# ═══════════════════════════════════════════════════════════════════

def test_an_unknown_switch_raises_rather_than_returning_false():
    """systemic_risk_engine.py:80 guessed a key name, guessed wrong, returned
    falsy for a year and passed every test. A rules layer that repeated that
    mistake would be an unusually poor joke."""
    with pytest.raises(R.UnknownSwitch):
        R.rule_on({}, "sct_flag_boosts_liv")
    with pytest.raises(R.UnknownSwitch):
        R.rule_on({R.RULES_FLAG: "2026.10"}, "not_a_switch")


def test_the_version_key_is_invisible_to_the_flag_reader():
    """A setting is not a decision flag. The key is underscore-prefixed so
    flag_utils.collect_all_flags skips it (flag_utils.py:30); if it ever became
    visible it would appear in every fixture's flag list and in calculate_mr's
    input."""
    from flag_utils import collect_all_flags
    assert R.RULES_FLAG.startswith("_")
    # NB the control name deliberately does NOT contain the substring "flag":
    # collect_all_flags routes any key containing "flag" down its list/str branch
    # (flag_utils.py:36-40), so a BOOLEAN whose name contains "flag" is silently
    # dropped. No declared or registered flag name contains it today — checked —
    # so nothing is affected, but a control named "real_flag" would have made this
    # test fail for a reason that has nothing to do with the rules version.
    collected = collect_all_flags({R.RULES_FLAG: "2026.10", "a_real_marker": True})
    assert R.RULES_FLAG not in collected
    assert "a_real_marker" in collected


def test_stamp_always_records_a_version():
    """A persisted round with no version is a round nobody can replay with
    confidence, so an empty stamp writes the baseline rather than nothing."""
    assert R.stamp({}, "2026.10")[R.RULES_FLAG] == "2026.10"
    assert R.stamp({}, None)[R.RULES_FLAG] == R.DEFAULT_RULES_VERSION
    assert R.stamp({}, "")[R.RULES_FLAG] == R.DEFAULT_RULES_VERSION


# ═══════════════════════════════════════════════════════════════════
#  THE WIRING — the version has to actually reach the engine
# ═══════════════════════════════════════════════════════════════════

def test_the_router_carries_the_version_through_to_post_tick():
    """The post-tick engines read behaviour off the flag bag, and
    engine._assemble_global_state rebuilds that bag from this round's events. A
    revival that fired in the tick but not in post_tick would be worse than one
    that never fired at all, so the key has to be in _PERSISTENT_FLAG_KEYS."""
    import ast
    src = (Path(__file__).resolve().parent.parent / "router.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "_PERSISTENT_FLAG_KEYS"):
            names = [e.id for e in node.value.elts if isinstance(e, ast.Name)]
            assert "_RULES_FLAG" in names, (
                "router._PERSISTENT_FLAG_KEYS no longer forwards the rules version; "
                "post_tick would run a revived mechanic on the baseline, or the "
                "reverse")
            return
    pytest.fail("router._PERSISTENT_FLAG_KEYS not found")


@pytest.mark.asyncio
async def test_a_new_session_records_its_rule_set():
    """A finished session has to say which rules produced its numbers. Without
    this a replay is guesswork."""
    import os
    os.environ.setdefault("USE_MEMORY_DB", "true")
    import database_memory as db
    session = await db.create_session("rules-version-probe", "facilitator-x")
    info = await db.get_session_info(session["session_id"])
    assert info.get("rules_version") == R.CURRENT_VERSION


def test_the_version_survives_a_whole_game_into_the_persisted_flags():
    """The stamp has to still be there at R10, or a finished session cannot say
    which rules produced its numbers — and a replay would guess.

    Driven through tests/golden_matrix_harness, which replicates the router's
    commit sequence step by step including the stamp (router.py:2966), the
    _forward_persistent_flags carry (router.py:3121) and the three-way merge.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import golden_matrix_harness as H

    for version in ("2026.09", "2026.10"):
        gs, _ = H.final_state("legacy_mixed", rules_version=version)
        flags = gs.get("active_event_flags") or {}
        assert flags.get(R.RULES_FLAG) == version, (
            f"a {version} session ends carrying {flags.get(R.RULES_FLAG)!r}")
        assert R.resolve_version(gs) == version
        # …and the switches resolve from the persisted state, not from a default
        # that happens to agree with it.
        expected = R.RULE_SETS[version].switches
        for switch, on in expected.items():
            assert R.rule_on(gs, switch) is on


def test_each_switch_can_be_assessed_on_its_own():
    """The point of NAMED switches rather than one "new rules" flag: Phase 5 has
    to be able to cost each mechanic separately, and a set of switches that only
    works all-or-nothing would not let it.

    This also produces the per-switch delta table Phase 5 needs, and asserts the
    property that makes the table meaningful — that the switches are separable,
    i.e. no switch is inert on its own and none depends on another being on.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import golden_matrix_harness as H

    baseline = {name: H.run_path(name, rules_version="2026.09") for name in H.PATHS}
    moved_by: dict[str, list[str]] = {}

    for switch in sorted(R.SWITCHES):
        version = f"_probe_{switch}"
        R.RULE_SETS[version] = R.RuleSet(
            version=version, note="one switch, for the separability check",
            switches={k: (k == switch) for k in R.SWITCHES},
            # The BASELINE calibration, so this measures the switch and not a
            # missing knob. A rule set with no calibration raises UnknownKnob at
            # the first read, which is the design working — the numbers are part
            # of a rule set, not an optional extra.
            calibration=dict(R.RULE_SETS[R.DEFAULT_RULES_VERSION].calibration),
        )
        try:
            moved_by[switch] = [
                name for name in H.PATHS
                if H.run_path(name, rules_version=version) != baseline[name]
            ]
        finally:
            R.RULE_SETS.pop(version, None)

    inert = sorted(s for s, paths in moved_by.items() if not paths)
    # Two switches genuinely cannot move the matrix, and both are recorded as such
    # rather than treated as failures — but WHICH two was measured, not assumed,
    # and the first guess was wrong twice over:
    #
    #   debrief_reads_option_flags  is consumed by the CEO interview and the two
    #       side tracks, none of which the ten-round matrix drives. Direct tests
    #       instead.
    #   biodiversity_audit_gate_reads_flags  changes the species-risk gate, and
    #       species_risk_score has no consumer outside biodiversity_engine: the
    #       stakeholder engines read water_stress_index and tnfd_disclosure_level
    #       from biodiversity_state, not species risk. Diagnostic only.
    #
    # npc_betrayal_reads_option_flags was expected here and is NOT inert:
    # stakeholder_memory_enabled defaults ON, not off, so the revival moves the
    # escalation surface on all seven paths. That correction came from this test.
    expected_inert = {"debrief_reads_option_flags",
                      "biodiversity_audit_gate_reads_flags"}
    assert set(inert) == expected_inert, (
        f"switches that move nothing in the matrix: {inert}\n"
        f"expected exactly {sorted(expected_inert)} — a NEW one here is either a "
        "switch that is not wired, or one whose effect the matrix cannot see, and "
        "the second case needs a direct test rather than silence.")

    for switch, paths in sorted(moved_by.items()):
        if switch in expected_inert:
            continue
        assert paths, f"{switch} moves nothing"
