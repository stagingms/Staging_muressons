"""Muressons — bidirectional flag reachability (Phase 3 of the dead-flag remediation).

THE INVARIANT THIS REPLACES
    tests/test_flag_sweep.py asserts that a declared flag's NAME appears somewhere
    in the source. That is the second generation of the question and it is green
    while blind for a fourth time, because a name is not a value:
    systemic_risk_engine.py:71 holds the literal "supply_chain_disruption_risk":
    -10.0 on a non-comment line in backend non-test code, so the sweep marks the
    flag READ, and the value has never once flowed. Closing blindness modes one at
    a time is a losing game — there is an unbounded supply of ways for a name to
    appear without a value arriving. This module asks the other question, at
    runtime: does the value reach a consumer, and does the consumer do anything?

WHAT IT ASSERTS, IN BOTH DIRECTIONS
    Forward   every flag Appendix B calls LIVE must be observed to move something.
    Reverse   every flag Appendix B calls DEAD must be observed to move nothing.
    Symmetry  and the set of flags that fail the naive rule "every declared flag
              must reach a consumer" must equal the DEAD set EXACTLY — no false
              alarms, no blind spots. That symmetry is the acceptance criterion for
              this phase, and test_the_naive_assertion_fails_for_exactly_the_dead_set
              is where it lives.

    The expectation table below is Appendix B §B.16 transcribed with its citations,
    which makes it a specification rather than a record of today's behaviour: a
    divergence is either a defect in the engine or an error in the appendix, and
    both must be surfaced. Two already were, and both are recorded here with their
    evidence rather than quietly accommodated.

HOW A VERDICT IS REACHED — see tests/flag_probe.py for the mechanics
    The DIFFERENTIAL is the verdict: scrub the flag out of existence, re-run the
    paths that raise it, diff the whole trace. It is shape-agnostic, which matters
    because three of Appendix B's LIVE flags move nothing but stakeholder
    attitudes, through a consumer that iterates the namespace in bulk and performs
    no keyed read at all. A keyed-read probe alone would report them dead — the
    exact false alarm the symmetry criterion forbids.

    The READ PROBE is the diagnosis: it records every keyed read of a flag name
    with its file:line and whether it returned truthy. That is what separates a
    dead flag with a consumer (READ_NEVER_TRUE — a defect; the effect was designed
    and has never run) from a dead flag with no consumer at all (NOT_READ — a
    choice marker, or a retirement candidate). Appendix B's §4 triage was done by
    hand; this derives it.

WHAT THIS MODULE DOES NOT COVER, STATED RATHER THAN IMPLIED
    The matrix drives the legacy_abc paradigm on seven paths. Pillar and healthcare
    paradigms are out of scope and their flags are not asserted here. One flag,
    full_materiality_alignment, is live only in the advanced_climate paradigm; it
    is declared scoped rather than dead, and test_the_paradigm_scoped_flag_is_live_
    behind_its_gate proves the door rather than asserting past it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import flag_probe as P                     # noqa: E402
import golden_matrix_harness as H          # noqa: E402
from flags.registry import REGISTRY, DEAD_DEFECT, by_status   # noqa: E402


# ═══════════════════════════════════════════════════════════════════
#  THE SPECIFICATION — Appendix B §B.16, transcribed with citations
# ═══════════════════════════════════════════════════════════════════
LIVE, DEAD, SCOPED = "LIVE", "DEAD", "SCOPED"

# disposition: what §4 of the remediation plan says to DO about it.
#   LIVE    nothing; it works
#   REVIVE  a consumer exists and the storage format hides it — fix the shape
#   RETIRE  no consumer and none intended; delete the flag
#   INERT   no consumer by design; the option's effect is in its impacts
#   PILLAR  live in the pillar paradigm, dead on the default path
#   SCOPED  live in another paradigm; not asserted by this matrix
_EXPECTED: dict[str, tuple[str, str, str]] = {
    # flag                            expected  disposition  Appendix B citation
    "electronics_blindspot":          (LIVE, "LIVE",   "B.2 / B.16 #1  — doubles R4 crisis, round_logic.py:227"),
    "deep_audit_completed":           (LIVE, "REVIVE", "B.2 / B.16 #2  — LIVE via sentiment; 4 unreachable readers"),
    "deferred_audit":                 (LIVE, "LIVE",   "B.2 / B.16 #3  — x1.5 R4 crisis, round_logic.py:234"),
    "full_materiality_alignment":     (SCOPED, "SCOPED", "B.3 / B.16 #4  — engine.py:3787, advanced_climate only"),
    "materiality_exceptions":         (DEAD, "INERT",  "B.3 / B.16 #5  — case (ii), choice marker"),
    "ceo_only_signoff":               (DEAD, "INERT",  "B.3 / B.16 #6  — case (i/ii), choice marker"),
    "supply_chain_disruption_risk":   (DEAD, "REVIVE", "B.4 / B.16 #7  — systemic_risk_engine.py:71 -10 SCT, unreachable"),
    "early_decarboniser":             (LIVE, "LIVE",   "B.4 / B.16 #8  — +0.10 synergy at R7, round_logic.py:2508"),
    "green_bond_active":              (DEAD, "RETIRE", "B.4 / B.16 #9  — the bond is priced by the R2 tier flags"),
    "carbon_deferred":                (LIVE, "LIVE",   "B.4 / B.16 #10 — sentiment; engine.py:3951 not on this path"),
    "remediation_active":             (DEAD, "REVIVE", "B.5 / B.16 #11 — systemic_risk_engine.py:73 +8 SCT, unreachable"),
    "pr_containment":                 (DEAD, "INERT",  "B.5 / B.16 #12 — case (ii), choice marker"),
    "deny_and_deflect":               (LIVE, "REVIVE", "B.5 / B.16 #13 — LIVE on sentiment; 2 unreachable readers"),
    "hard_engineering":               (DEAD, "REVIVE", "B.6 / B.16 #14 — SEE _APPENDIX_B_CORRECTIONS; B says LIVE"),
    "nature_based_resilience":        (LIVE, "LIVE",   "B.6 / B.16 #15 — Adaptation Premium, ending_pathways.py:566"),
    "insurance_only":                 (LIVE, "LIVE",   "B.6 / B.16 #16 — blocks Resilience Champion, terminal_valuation.py:233"),
    "ai_monetised":                   (LIVE, "LIVE",   "B.7 / B.16 #17 — EU AI Act liability, round_logic.py:2196"),
    "ethical_ai_overhaul":            (LIVE, "REVIVE", "B.7 / B.16 #18 — LIVE (Truth Premium); SDG 16 +15 unreachable"),
    "quiet_patch":                    (LIVE, "LIVE",   "B.7 / B.16 #19 — sentiment only, -10 across five stakeholders"),
    "circular_redesign":              (DEAD, "PILLAR", "B.8 / B.16 #20 — case (iii); SDG 12 +15 and +5 SCT unreachable"),
    "epr_program":                    (DEAD, "REVIVE", "B.8 / B.16 #21 — systemic_risk_engine.py:75 +3 SCT, unreachable"),
    "waste_to_energy":                (DEAD, "PILLAR", "B.8 / B.16 #22 — case (iii), pillar exclusivity only"),
    "synergy_unlock":                 (LIVE, "LIVE",   "B.8 / B.16 #23 — up to +0.15 M_R, terminal_valuation.py:213"),
    "water_efficiency_all":           (DEAD, "PILLAR", "B.9 / B.16 #24 — case (iii), reads r8_pillar_flags only"),
    "electronics_water_priority":     (LIVE, "LIVE",   "B.9 / B.16 #25 — blocks Resilience Champion"),
    "desalination_built":             (DEAD, "PILLAR", "B.9 / B.16 #26 — case (iii), pillar negative guard"),
    "immediate_closure":              (DEAD, "PILLAR", "B.10 / B.16 #27 — case (iii), impact_engine.py:294 pillar-gated"),
    "managed_transition":             (LIVE, "LIVE",   "B.10 / B.16 #28 — Just Transition premium +0.12"),
    "community_fund":                 (LIVE, "REVIVE", "B.10 / B.16 #29 — LIVE (+0.18); SDG 1 +10 unreachable"),
    "resist_integrate":               (DEAD, "RETIRE", "B.11 / B.16 #30 — R10 effects come from impacts, not the flag"),
    "spinoff":                        (DEAD, "RETIRE", "B.11 / B.16 #31 — as resist_integrate"),
    "divest":                         (DEAD, "RETIRE", "B.11 / B.16 #32 — as resist_integrate"),
}

# B.16 #33, turnaround_restructuring, is declared on Option T and no ten-round
# path can raise it. It is excluded by construction rather than by opinion, and
# test_the_expectation_table_covers_the_declared_surface proves that is the only
# declared flag the table omits.

# ── Where this module and Appendix B disagree, with the evidence ────────────
# Both were found by the probe and verified independently of it. They are
# recorded here rather than accommodated, because a specification that quietly
# bends to the implementation stops being a specification.
_APPENDIX_B_CORRECTIONS = {
    "hard_engineering": (
        "Appendix B §B.6 and §B.16 #14 call it LIVE, on the strength of its ONE "
        "consumer: round_logic._revert_r5_hard_engineering_pulse (:3509-3534), "
        "which is supposed to reverse the +3 carbon-intensity construction pulse "
        "at R7. That consumer cannot fire. It reads `gs.get('active_event_flags')` "
        "(:3518) — but post_tick receives the POST-TICK state, whose flag bag "
        "engine._assemble_global_state set to this round's events (engine.py:4472, "
        ":4905) plus the seven session keys _forward_persistent_flags carries "
        "(router.py:2370-2392). r5_flags is not among them; the history lives in "
        "`previous_flags`, which post_tick also receives and which every OTHER "
        "flattened reader in the file uses (:423, :2195, :2507, :2537, :2666, "
        ":2675, :2683, :2690). Measured at R7 on the all_a path: the collected set "
        "the function sees is ['greenwashing_checked', 'technology_lockin_penalty'] "
        "and the reversal never applies, so the +3 pulse is permanent — which is "
        "the exact defect FLAG-8/WP-23 believed it had fixed when it replaced the "
        "top-level test with the flattened one. It swapped the reader and left the "
        "container wrong.\n"
        "        This is a FOURTH defect shape, not one of the three the "
        "remediation plan names: right reader, right key, WRONG GENERATION of the "
        "container. It belongs in Appendix B §B.13's structurally-unreachable "
        "table as a 23rd finding, and hard_engineering's B.16 row should read "
        "DEAD (REVIVE)."
    ),
}

# ── The paradigm gate, proved rather than asserted past ────────────────────
_PARADIGM_SCOPED = {
    "full_materiality_alignment": (
        "advanced_climate",
        "engine.py:3763 opens `if ctx.decision_paradigm == \"advanced_climate\":` "
        "and the flag's only consumer is inside it at :3787, scaling NCD "
        "forgiveness by 1.25. The matrix runs legacy_abc, so the site is "
        "unreachable here for a reason that has nothing to do with the flag. "
        "Appendix B §B.3 names the paradigm; the §B.16 summary row does not, which "
        "is what makes the flat 'LIVE' misleading. "
        "test_the_paradigm_scoped_flag_is_live_behind_its_gate runs the door."
    ),
}

_EXPECTED_LIVE = {f for f, (e, _, _) in _EXPECTED.items() if e == LIVE}
_EXPECTED_DEAD = {f for f, (e, _, _) in _EXPECTED.items() if e == DEAD}
_EXPECTED_SCOPED = {f for f, (e, _, _) in _EXPECTED.items() if e == SCOPED}

# The six structurally-unreachable consumers of Appendix B §B.13, as file:line and
# the flags each hides. Asserted individually below, because "the defect is still
# there" is a claim that should be made precisely enough to fail when it is fixed.
# NOTE ON LINE NUMBERS. These are exact on purpose: a consumer that MOVED and a
# consumer that was DELETED must not look the same to this test, and only the line
# tells them apart. The cost is that editing anything above one of these sites
# fails here until the number is updated, which has happened three times across
# Phases 3-4. The fix each time is one line, and the failure message names the new
# location, so the churn is cheap and the alternative — matching on the function
# name — would silently accept a read that moved into a different branch.
# ═══════════════════════════════════════════════════════════════════
#  THE STRUCTURALLY-UNREACHABLE CONSUMERS
# ═══════════════════════════════════════════════════════════════════
# Keyed on (file, SOURCE TEXT of the read), not (file, line number).
#
# The requirement this table has always had is that a MOVE must not break it and
# a CHANGE must. A line number gets that exactly backwards, and the cost was
# real: round_logic's anchor churned 3523 -> 3567 -> 3596 -> 3598 -> 3607 across
# Phases 3-5, five edits, none of them describing a change to the read. Every one
# of those was a chance to "fix" the test by moving a number without looking at
# what moved. The other lint in this suite (test_no_stringified_flag_reads.py)
# already anchors on the expression rather than the line, and says why; this
# table now does the same.
#
# The text is the stripped source of the line the probe records for the read, and
# each one is asserted unique in its file below — an ambiguous anchor would be a
# weaker test, quietly.
_UNREACHABLE_CONSUMERS = {
    # Phase 4's fog-of-war work moved this read without changing it: it is still
    # a top-level key test against a list-held flag, still false forever. Only
    # the 2026.10 branch asks the flattened reader.
    ("engine.py", 'deep_audit = "deep_audit_completed" in _fog_flags'):
        ({"deep_audit_completed"},
         "shape A — container mismatch: a top-level key test against a list-held flag"),
    ("engine.py", "if flags.get(flag_key):"):
        ({"circular_redesign", "community_fund", "ethical_ai_overhaul"},
         "shape B — wrong source dict: _SDG_FLAG_BONUSES reads ctx.events, empty at engine.py:5055"),
    # Phase 4 moved this read into _transparency_flag_reader's 2026.09 branch, so
    # the LINE changed and the READ did not: still `name in flags` against the
    # raw bag, still against a flag held inside a list, still never true. The
    # branch is deliberately a per-flag membership test on the dict rather than a
    # precomputed set, because collapsing it would be behaviourally identical and
    # would make the defect invisible to this probe.
    ("systemic_risk_engine.py", "return lambda name: name in flags or name in legacy"):
        ({"deep_audit_completed", "supply_chain_disruption_risk",
          "deny_and_deflect", "remediation_active",
          "circular_redesign", "epr_program"},
         "shape C — guessed key name: flags.get('flags_set') has no writer"),
    ("round_logic.py",
     'if round_number == 7 and ("hard_engineering" in _held or flags.get("hard_engineering")) \\'):
        ({"hard_engineering"},
         "shape D — wrong generation: the post-tick flag bag holds this round's events only"),
}

_SOURCE_CACHE: dict[str, list[str]] = {}


def _source_lines(file: str) -> list[str]:
    if file not in _SOURCE_CACHE:
        _SOURCE_CACHE[file] = (_BACKEND / file).read_text(encoding="utf-8").splitlines()
    return _SOURCE_CACHE[file]


def _anchor(file: str, line: int) -> tuple[str, str]:
    """The (file, source text) key for a probe-recorded site."""
    lines = _source_lines(file)
    text = lines[line - 1].strip() if 0 < line <= len(lines) else f"<line {line} gone>"
    return (file, text)


def _anchors_of(sites) -> set[tuple[str, str]]:
    return {_anchor(s.file, s.line) for s in sites}


def test_every_unreachable_anchor_is_unique_in_its_file():
    """An anchor that matches two lines would silently weaken the four tests
    below — they would pass on the wrong site."""
    for file, text in _UNREACHABLE_CONSUMERS:
        hits = [i + 1 for i, line in enumerate(_source_lines(file)) if line.strip() == text]
        assert len(hits) == 1, (
            f"{file}: the anchor {text!r} matches {len(hits)} lines {hits}. Widen it "
            "(or, if the site is gone, move the flag's row out of "
            "_UNREACHABLE_CONSUMERS and _EXPECTED in the same commit).")


# ═══════════════════════════════════════════════════════════════════
#  FIXTURES — one probed run and one differential sweep for the module
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def observation():
    """The read probe under the BASELINE rule set. Every _UNREACHABLE_CONSUMERS
    assertion below is a statement about 2026.09: those are the reads that are
    still broken for every session played to date."""
    return P.observe(rules_version="2026.09")


@pytest.fixture(scope="module")
def verdicts():
    """Differential verdicts under the baseline rule set."""
    results = P.differential(sorted(_EXPECTED), rules_version="2026.09")
    return {flag: P.moved_anywhere(res) for flag, res in results.items()}


@pytest.fixture(scope="module")
def verdicts_revived():
    """Differential verdicts with every Phase 4 switch ON."""
    results = P.differential(sorted(_EXPECTED), rules_version="2026.10")
    return {flag: P.moved_anywhere(res) for flag, res in results.items()}


# The five flags Phase 4 brings back, and the switch that does it. This is the
# other half of the phase's exit condition: the probe must be green under both
# rule sets, which means it has to know which flags are supposed to CHANGE
# verdict between them — a revival nobody declared is as much a failure as a
# revival that did not happen.
_REVIVED_BY_PHASE_4 = {
    "supply_chain_disruption_risk": "sct_flag_boosts_live",
    "remediation_active":           "sct_flag_boosts_live",
    "epr_program":                  "sct_flag_boosts_live",
    # circular_redesign's +5 transparency is absorbed by the clamp on every path
    # that raises it (see test_the_shape_c_repair_drives_the_score_into_its_clamps);
    # what revives it is the SDG 12 +15, which moves the report.
    "circular_redesign":            "sdg_flag_bonuses_live",
    "hard_engineering":             "hard_engineering_pulse_revert_live",
}


# ═══════════════════════════════════════════════════════════════════
#  THE TABLE ITSELF MUST STAY HONEST
# ═══════════════════════════════════════════════════════════════════

def test_the_expectation_table_covers_the_declared_surface():
    """Adding an option flag to round_configs must fail here until someone rules
    on it. This is the "cannot rot in either direction" half that the taxonomy
    docstring promises and the sweep never delivered."""
    declared = {f for r in range(1, H.N_ROUNDS + 1)
                for opt in (H.get_round_config(r).get("options") or {}).values()
                for f in (opt.get("flags_set") or [])}
    missing = sorted(declared - set(_EXPECTED))
    extra = sorted(set(_EXPECTED) - declared)
    assert not missing, (
        f"{len(missing)} declared round flags have no ruling in _EXPECTED: {missing}\n"
        "Every flag a round can raise needs an expected verdict, a disposition and "
        "an Appendix B citation before it ships.")
    assert not extra, f"_EXPECTED rules on flags no round declares: {extra}"


def test_every_matrix_flag_is_actually_raised_by_some_path():
    """A verdict on a flag the matrix never raises is an opinion, not a
    measurement. The coverage ratchet in test_option_matrix_golden keeps the
    (round, option) pairs covered; this keeps the FLAGS covered."""
    obs = P.observe()
    never = sorted(f for f in _EXPECTED if not obs.written(f))
    assert not never, (
        f"the matrix raises no path that sets {never}; their verdicts below would "
        "be unmeasured. Add a path to golden_matrix_harness.PATHS.")


# ═══════════════════════════════════════════════════════════════════
#  FORWARD — every LIVE flag moves something
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("flag", sorted(_EXPECTED_LIVE))
def test_every_live_flag_changes_the_run(flag, verdicts, observation):
    assert verdicts[flag], (
        f"{flag} is declared LIVE ({_EXPECTED[flag][2]}) and scrubbing it out of "
        f"the namespace changed nothing anywhere in the matrix.\n\n"
        f"{observation.explain(flag)}\n\n"
        "Either its consumer stopped firing, or the path that exercised it stopped "
        "reaching that consumer. Both are regressions.")


# ═══════════════════════════════════════════════════════════════════
#  REVERSE — every DEAD flag moves nothing, and is diagnosed
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("flag", sorted(_EXPECTED_DEAD))
def test_every_dead_flag_changes_nothing(flag, verdicts, observation):
    assert not verdicts[flag], (
        f"{flag} is declared DEAD ({_EXPECTED[flag][2]}) and scrubbing it changed "
        f"the run — so something now reads it.\n\n{observation.explain(flag)}\n\n"
        "If a fix revived it deliberately, move it to LIVE in _EXPECTED in the same "
        "commit. A revival nobody recorded is how the last registry rotted.")


@pytest.mark.parametrize("flag", sorted(_EXPECTED_DEAD))
def test_the_dead_flags_are_diagnosed_not_merely_reported(flag, observation):
    """REVIVE means a consumer exists and the storage format hides it; RETIRE,
    INERT and PILLAR mean no consumer runs on this path. The probe's read record
    has to agree with the disposition, because the disposition is what §4 of the
    remediation plan schedules work from."""
    disposition = _EXPECTED[flag][1]
    verdict = observation.verdict(flag)
    if disposition == "REVIVE":
        assert verdict == P.READ_NEVER_TRUE, (
            f"{flag} is scheduled REVIVE because a consumer is supposed to exist, "
            f"but the probe saw {verdict}: {observation.reads(flag)} keyed reads.\n"
            f"{observation.explain(flag)}")
    else:
        assert verdict in (P.NOT_READ, P.READ_NEVER_TRUE), (
            f"{flag} is {disposition} and the probe reports {verdict}")


# ═══════════════════════════════════════════════════════════════════
#  SYMMETRY — the acceptance criterion for this phase
# ═══════════════════════════════════════════════════════════════════

def test_the_naive_assertion_fails_for_exactly_the_dead_set(verdicts):
    """THE EXIT CONDITION.

    Apply the rule a correct engine would satisfy — every flag a round declares
    must change something — and collect what fails. That set must be Appendix B's
    dead set EXACTLY. One flag too many is a false alarm and the probe cannot be
    trusted to gate a fix. One too few is a blind spot and the probe cannot be
    trusted to find one.
    """
    failures = {flag for flag, moved in verdicts.items() if not moved}
    expected = _EXPECTED_DEAD | _EXPECTED_SCOPED

    false_alarms = sorted(failures - expected)
    blind_spots = sorted(expected - failures)
    assert not false_alarms, (
        f"the probe reports {false_alarms} dead and the specification does not.\n"
        "Either the engine regressed or the probe cannot see a live consumer — and "
        "a probe with a false alarm cannot gate the remediation.")
    assert not blind_spots, (
        f"the specification calls {blind_spots} dead and the probe sees them move.\n"
        "Either they were revived without the table being updated, or the "
        "differential is detecting something other than the flag.")


# ═══════════════════════════════════════════════════════════════════
#  PHASE 4 — the same probe, under the revived rule set
# ═══════════════════════════════════════════════════════════════════

def test_the_baseline_rule_set_revives_nothing(verdicts):
    """The compatibility guarantee, from the probe's side. Every switch is off in
    2026.09, so every flag Phase 4 revives must still read dead there — which is
    what lets a past cohort's score stand."""
    leaked = sorted(f for f in _REVIVED_BY_PHASE_4 if verdicts[f])
    assert not leaked, (
        f"{leaked} move under the BASELINE rules. A revival has escaped its "
        "switch, and every session already scored under 2026.09 is now wrong.")


@pytest.mark.parametrize("flag", sorted(_REVIVED_BY_PHASE_4))
def test_each_revival_actually_revives_its_flag(flag, verdicts, verdicts_revived):
    """A switch that changes nothing is not a revival. Each of these has to be
    dead under 2026.09 and alive under 2026.10 — the phase's exit condition,
    per flag."""
    switch = _REVIVED_BY_PHASE_4[flag]
    assert not verdicts[flag], f"{flag} was already live under the baseline"
    assert verdicts_revived[flag], (
        f"{flag} is supposed to come back when {switch} is on, and scrubbing it "
        f"under 2026.10 still changes nothing.\n"
        f"{P.observe(rules_version='2026.10').explain(flag)}")


def test_the_revived_rule_set_revives_exactly_the_declared_set(verdicts, verdicts_revived):
    """THE PHASE 4 EXIT CONDITION, as a set equality.

    Green under 2026.09 with the switches off, green under 2026.10 with them on —
    and the difference between the two must be exactly the flags this module
    names, no more and no fewer. A flag that quietly came back is a mechanic
    nobody costed; a flag that did not is a switch that is not wired.
    """
    revived = {f for f in _EXPECTED if verdicts_revived[f] and not verdicts[f]}
    lost = {f for f in _EXPECTED if verdicts[f] and not verdicts_revived[f]}

    assert revived == set(_REVIVED_BY_PHASE_4), (
        f"  unexpected revivals: {sorted(revived - set(_REVIVED_BY_PHASE_4))}\n"
        f"  failed revivals    : {sorted(set(_REVIVED_BY_PHASE_4) - revived)}")
    assert not lost, (
        f"turning the revivals on KILLED {sorted(lost)}. A rules change may add "
        "behaviour; it may not silently remove some.")


def test_the_still_dead_flags_are_dead_for_a_reason_that_survives_the_revival(verdicts_revived):
    """What is left dead once every switch is on, and why. These are the flags
    §4.2 and §4.3 of the remediation plan rule RETIRE or INERT, plus the
    pillar-mode ones the legacy matrix cannot reach — none of them is waiting for
    a fix, and this is the list Phase 5 signs off rather than re-investigates."""
    still_dead = sorted(f for f in _EXPECTED_DEAD if not verdicts_revived[f])
    dispositions = {f: _EXPECTED[f][1] for f in still_dead}
    unexplained = sorted(f for f, d in dispositions.items()
                         if d not in ("RETIRE", "INERT", "PILLAR"))
    assert not unexplained, (
        f"{unexplained} are still dead with every switch on, and their disposition "
        f"says a consumer was supposed to come back: "
        f"{ {f: dispositions[f] for f in unexplained} }")


# ═══════════════════════════════════════════════════════════════════
#  THE SIX UNREACHABLE CONSUMERS, EACH AT ITS OWN LINE
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("location", sorted(_UNREACHABLE_CONSUMERS))
def test_the_unreachable_consumer_is_still_unreachable(location, observation):
    """Appendix B §B.13's structurally-unreachable table, held as executable fact.

    Each of these is a real read of a real flag that has never once returned true.
    When Phase 4 fixes one, this fails — which is the point: the fix has to move
    the specification with it.
    """
    flags, shape = _UNREACHABLE_CONSUMERS[location]
    file, text = location
    for flag in sorted(flags):
        assert location in _anchors_of(observation.sites(flag)), (
            f"{flag} is no longer read at {file} by `{text}` — the consumer was "
            f"deleted, the read was rewritten, or it stopped executing on the "
            f"matrix paths. (A move alone cannot cause this.)\n"
            f"{observation.explain(flag)}")
        assert location not in _anchors_of(observation.true_site_list(flag)), (
            f"{file} `{text}` now sees {flag} TRUE. If that was the intended fix "
            f"({shape}), remove this location from _UNREACHABLE_CONSUMERS and move "
            f"the flag's row in _EXPECTED in the same commit.")


def test_the_three_defect_shapes_are_each_still_represented(observation):
    """The remediation plan's argument is that these are one fault with three
    surface shapes, not sixteen bugs. If a shape disappears from the codebase the
    argument needs revisiting, and if a new one appears it needs naming — as
    round_logic.py:3523 did."""
    for location, (flags, shape) in _UNREACHABLE_CONSUMERS.items():
        file, text = location
        seen = [f for f in flags if location in _anchors_of(observation.sites(f))]
        assert seen, f"no flag is read at {file} by `{text}` any more ({shape})"


# ═══════════════════════════════════════════════════════════════════
#  THE DISAGREEMENTS WITH APPENDIX B
# ═══════════════════════════════════════════════════════════════════

def test_hard_engineering_reads_the_wrong_generation_of_the_flag_bag():
    """The correction recorded in _APPENDIX_B_CORRECTIONS, proved without the probe.

    Drive the all_a path — R5 option_a, the only option that sets
    hard_engineering — and look at what _revert_r5_hard_engineering_pulse actually
    sees at R7. If it ever sees the flag, Appendix B was right and this module's
    table is wrong.
    """
    import round_logic
    from flag_utils import collect_all_flags

    seen: list[dict] = []
    original = round_logic._revert_r5_hard_engineering_pulse

    def spy(gs, bus, extra, round_number, prev_flags=None):
        result = original(gs, bus, extra, round_number, prev_flags)
        if round_number == 7:
            flags = gs.get("active_event_flags") or {}
            seen.append({
                "collected": sorted(collect_all_flags(dict(flags))),
                "top_level": flags.get("hard_engineering"),
                "reverted": extra.get("hard_engineering_pulse_reverted"),
            })
        return result

    round_logic._revert_r5_hard_engineering_pulse = spy
    try:
        # Under the BASELINE rules. Phase 4 wired the fix behind
        # hard_engineering_pulse_revert_live; this is the state a 2026.09 session
        # is still in, and the state every session played to date was scored in.
        H.final_state("all_a", rules_version="2026.09")
    finally:
        round_logic._revert_r5_hard_engineering_pulse = original

    assert seen, "the R7 revert never ran; this test no longer measures anything"
    # The defect is the CONTAINER, not the reader: what post_tick hands this
    # function has never held r5_flags. Phase 4's fix passes previous_flags in
    # alongside it rather than changing what it reads from gs.
    for obs in seen:
        assert "hard_engineering" not in obs["collected"], (
            "the R7 revert now sees hard_engineering — the shape-D defect is fixed. "
            "Move hard_engineering to LIVE in _EXPECTED, drop it from "
            "_UNREACHABLE_CONSUMERS and _APPENDIX_B_CORRECTIONS, and correct "
            "Appendix B §B.16 #14 in the same commit.")
        assert not obs["top_level"], "hard_engineering is now a top-level boolean too"
        assert not obs["reverted"], (
            "the +3 carbon-intensity pulse is being reverted after all")


def test_the_paradigm_scoped_flag_is_live_behind_its_gate():
    """full_materiality_alignment is declared SCOPED, not DEAD. A declaration that
    cannot be checked is a hole, so open the door: run the same tick under both
    paradigms and show the flag moves natural capital debt in one and not the
    other."""
    import copy
    from engine import process_tick

    def ncd_after(paradigm: str, with_flag: bool):
        gs = H.make_initial_global(1, "paradigm-probe")
        bus = H.make_initial_bus()
        gs["round_number"] = 3
        gs["pedagogical_overrides"] = dict(H.PED_OVERRIDES)
        if with_flag:
            gs["active_event_flags"]["r2_flags"] = ["full_materiality_alignment"]
        result = process_tick(
            current_global=copy.deepcopy(gs), current_bus=copy.deepcopy(bus),
            decisions=H._decisions(3, bus, H._spec_for("all_b")), dividends_paid=0,
            crisis_severity=0.0, imitation_decay_rate=0.10,
            decision_paradigm=paradigm,
        )
        return (round(sum(b.get("natural_capital_debt", 0) for b in result["bu_states"]), 3),
                result["events"].get("ncd_forgiveness_materiality_bonus"))

    legacy_off, legacy_bonus_off = ncd_after("legacy_abc", False)
    legacy_on, legacy_bonus_on = ncd_after("legacy_abc", True)
    climate_off, _ = ncd_after("advanced_climate", False)
    climate_on, climate_bonus = ncd_after("advanced_climate", True)

    assert legacy_off == legacy_on and legacy_bonus_off is legacy_bonus_on is None, (
        "full_materiality_alignment now moves NCD on the legacy path — it is no "
        "longer paradigm-scoped, so move it to LIVE in _EXPECTED")
    assert climate_on < climate_off, (
        "the advanced_climate consumer at engine.py:3787 has stopped applying the "
        f"1.25 NCD-forgiveness bonus: {climate_off} -> {climate_on}")
    assert climate_bonus == 1.25, f"the bonus is no longer 1.25 but {climate_bonus}"


# ═══════════════════════════════════════════════════════════════════
#  THE PROBE'S OWN HONESTY
# ═══════════════════════════════════════════════════════════════════

def test_observation_does_not_perturb_the_run(observation):
    """A probe that changes the run cannot describe it. Every instrumented path
    must reproduce its golden fixture exactly.

    This is not hypothetical care. The first version of the hooks wrapped
    new_global["active_event_flags"] and the events bag as two objects; production
    makes them ONE (engine.py:4472), and de-aliasing them moved group_reputation
    58 -> 63 at R2 on every path.
    """
    for name, trace in observation.traces.items():
        golden = H.load_golden(name)
        assert golden is not None, f"no fixture for path '{name}'"
        assert trace == golden[:-1], (
            f"the probe changed path '{name}':\n{H.first_diff(golden[:-1], trace)}")


def test_the_bulk_read_blind_spot_is_enumerated(observation):
    """The read probe cannot attribute a flag consumed in bulk. Rather than leave
    that implied, the census records every site that iterates the namespace — and
    the sentiment bridge, which is why three LIVE flags show no keyed read at all,
    must be in it. If this list ever empties, the probe has stopped watching."""
    assert observation.bulk, "the bulk census is empty; the probe is not recording"
    sites = {(s.file, s.op) for s in observation.bulk}
    assert ("engine.py", "items") in sites, (
        "engine.py:4791 builds the sentiment map's flag list by iterating "
        "ctx.events; that bulk read is the probe's blind spot and it must stay "
        "visible in the census")
    for flag in ("carbon_deferred", "quiet_patch"):
        assert observation.verdict(flag) == P.NOT_READ, (
            f"{flag} now has a keyed read; if a consumer was added, this test's "
            "premise — that the differential is what covers the bulk path — needs "
            "revisiting")


def test_the_differential_refuses_a_scrub_that_did_not_work():
    """The verdict "nothing moved" is only meaningful if the flag really was
    absent. flag_probe raises rather than reporting when a scrubbed flag is still
    visible; prove that guard is wired, because a silent scrub failure would turn
    every live flag into a false dead."""
    class _NoOpHooks(H.MatrixHooks):
        pass

    trace = H.run_path("all_a", hooks=_NoOpHooks())
    assert any("electronics_blindspot" in rec.get("flags", ())
               for rec in trace), (
        "all_a no longer raises electronics_blindspot, so the guard below is "
        "measuring nothing")
    # A scrub with the config patch but no container scrub must be caught. The
    # container scrub is what hides a flag the engine re-writes as a top-level
    # boolean, so this is the case the guard exists for.
    with pytest.raises(AssertionError, match="scrub of 'ai_monetised'.*still"):
        P.differential(["ai_monetised"], path_names=["all_a"], baselines=None,
                       _hooks_override=_NoOpHooks)


# ═══════════════════════════════════════════════════════════════════
#  FAULT INJECTION — the correctness test for the probe itself
# ═══════════════════════════════════════════════════════════════════

# systemic_risk_engine.calc_supply_chain_transparency's flag_boosts table, copied
# so the repaired version below stays a repair of THAT function and not a rewrite
# of it. The one changed line is the membership test.
_SCT_BOOSTS = {
    "deep_audit_completed": 20.0, "blockchain_traceability": 15.0,
    "materiality_aligned": 5.0, "supply_chain_disruption_risk": -10.0,
    "deny_and_deflect": -15.0, "remediation_active": 8.0,
    "circular_redesign": 5.0, "epr_program": 3.0,
}
# The three flags whose ONLY consumer anywhere is that function. Repairing it must
# bring exactly these back to life. circular_redesign is deliberately not here
# even though the same table gives it +5 — see the test.
_SHAPE_C_EXCLUSIVE = {"supply_chain_disruption_risk", "remediation_active", "epr_program"}


def _repaired_supply_chain_transparency(current_score, flags, round_number):
    """systemic_risk_engine.calc_supply_chain_transparency (:55-90) with shape C
    repaired and nothing else changed.

    The original tests `flag in flags or flag in flags.get("flags_set", [])`. Its
    author knew there were two storage shapes and wrote a fallback for the second
    one; they guessed the key name and guessed wrong — the writer's key is
    r{N}_flags (round_logic.py:3770) and nothing in the core tick writes
    "flags_set" onto the flag bag at all. This version asks the flattened reader
    instead, which is what the fix will do.
    """
    from flag_utils import collect_all_flags
    delta = -3.0
    held = collect_all_flags(dict(flags or {}))
    applied = {}
    for flag, boost in _SCT_BOOSTS.items():
        if flag in held:
            delta += boost
            applied[flag] = boost
    new_score = round(max(0, min(100, current_score + delta)), 2)
    return new_score, {"previous": current_score, "new": new_score,
                       "delta": round(delta, 2), "entropy": -3.0,
                       "boosts_applied": applied}


def test_repairing_shape_c_revives_exactly_the_flags_that_site_hides(verdicts):
    """If the probe cannot tell a fix from no fix, none of the verdicts above mean
    anything. So make one — the smallest real one — and check the probe notices it
    and notices nothing else.

    Repairing the ONE membership test at systemic_risk_engine.py:80 must bring
    back exactly the flags whose only consumer is that line, and must not disturb
    a single other verdict in either direction.
    """
    import systemic_risk_engine

    original = systemic_risk_engine.calc_supply_chain_transparency
    systemic_risk_engine.calc_supply_chain_transparency = _repaired_supply_chain_transparency
    try:
        repaired_baselines = {name: H.run_path(name) for name in H.PATHS}
        after = {flag: P.moved_anywhere(res) for flag, res in
                 P.differential(sorted(_EXPECTED), baselines=repaired_baselines).items()}
    finally:
        systemic_risk_engine.calc_supply_chain_transparency = original

    revived = {f for f in after if after[f] and not verdicts[f]}
    killed = {f for f in after if verdicts[f] and not after[f]}

    assert revived == _SHAPE_C_EXCLUSIVE, (
        f"repairing systemic_risk_engine.py:80 revived {sorted(revived)}; the flags "
        f"whose only consumer is that line are {sorted(_SHAPE_C_EXCLUSIVE)}.\n"
        f"  missed  : {sorted(_SHAPE_C_EXCLUSIVE - revived)} — the probe cannot see a fix\n"
        f"  spurious: {sorted(revived - _SHAPE_C_EXCLUSIVE)} — the probe attributes "
        "an effect to the wrong flag")
    assert not killed, (
        f"repairing one read killed {sorted(killed)}; a repair must not take a live "
        "flag with it")


def test_the_shape_c_repair_drives_the_score_into_its_clamps():
    """Why circular_redesign does NOT appear in _SHAPE_C_EXCLUSIVE, and a measured
    warning for whoever schedules the revival.

    The +5 the same table gives circular_redesign is real, and repairing the read
    still changes nothing — because by the round that flag is set the score has
    already reached a clamp. Measured with the repair in place: all_a runs
    27, 24, 21, 8, 3, 0, 0, 0, 0, 0 and legacy_mixed runs 27, 44, 61, 78, 100,
    100, 100, 100, 100, 100. Supply-chain transparency is a 0-100 score with a
    -3/round entropy and boosts up to +20, and it is not calibrated for those
    boosts to apply: the uniform-A path floors by R6 and the legacy path ceilings
    by R5.

    §5 of the remediation plan says reviving these flags changes every score
    because transparency feeds the nature premium, WACC and the exit multiple.
    This is the number behind that argument, and it says recalibration is part of
    the revival rather than a follow-up to it.
    """
    import systemic_risk_engine

    original = systemic_risk_engine.calc_supply_chain_transparency
    systemic_risk_engine.calc_supply_chain_transparency = _repaired_supply_chain_transparency
    try:
        series = {name: [rec["score"]["supply_chain_transparency"]
                         for rec in H.run_path(name)[:-1]]
                  for name in ("all_a", "legacy_mixed")}
    finally:
        systemic_risk_engine.calc_supply_chain_transparency = original

    assert series["all_a"][-1] == 0.0, (
        f"all_a no longer floors under the repair: {series['all_a']}")
    assert series["legacy_mixed"][-1] == 100.0, (
        f"legacy_mixed no longer ceilings under the repair: {series['legacy_mixed']}")
    assert 0.0 in series["all_a"] and 100.0 in series["legacy_mixed"], (
        "the clamps are no longer reached, so the calibration warning above is "
        "stale and should be re-measured")


# ═══════════════════════════════════════════════════════════════════
#  CROSS-CHECK AGAINST THE PHASE 2 REGISTRY
# ═══════════════════════════════════════════════════════════════════

def test_the_registry_and_the_probe_tell_the_same_story(verdicts, observation):
    """flags/registry.py was built in Phase 2 by reading the code. This module
    reaches its verdicts by running it. Where they disagree, one of them is wrong
    and someone has to look."""
    dead_in_registry = {spec.name for spec in by_status(DEAD_DEFECT)}
    disagreements = []
    for flag, moved in verdicts.items():
        if flag in _EXPECTED_SCOPED:
            continue
        registry_says_dead = flag in dead_in_registry
        probe_says_dead = not moved
        spec = REGISTRY.get(flag)
        if spec is None:
            disagreements.append(f"{flag}: not in the registry at all")
        elif registry_says_dead and not probe_says_dead:
            disagreements.append(
                f"{flag}: registry DEAD_DEFECT, probe sees it move "
                f"({observation.verdict(flag)})")
        elif probe_says_dead and spec.status == "LIVE":
            disagreements.append(
                f"{flag}: registry LIVE, probe sees it move nothing "
                f"({observation.verdict(flag)}) — {observation.explain(flag)}")
    assert not disagreements, (
        "the Phase 2 registry and the Phase 3 probe disagree:\n  "
        + "\n  ".join(disagreements))
