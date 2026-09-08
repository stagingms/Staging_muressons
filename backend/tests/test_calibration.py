"""Phase 5 — the recalibration, and the three constants that did NOT need it.

WHAT PHASE 5 WAS ASKED TO DO
    "Run the Monte Carlo stress harness under both rule sets. Re-derive the M_R
    ceilings, the clamp and the archetype thresholds."

WHAT THE MEASUREMENT SAID
    Three of those four instructions were answered NO, and the fourth found a
    problem the plan had not anticipated. 3,300 paired games (tests/stress_harness,
    seeds 1-3 swans-off and 11-13 swans-on, every run played under both rule sets):

      the 2.05 clamp        binds in 13 of 1,650 baseline runs and 11 revived —
                            0.8%, which is a safety net behaving like one. NOT
                            re-derived.
      archetype thresholds  the population split barely moves: REGENERATIVE_TITAN
                            9.5% -> 8.3%, SAFE_HAVEN 34.6% -> 33.2%,
                            STRANDED_RELIC 6.8% -> 8.0%. Re-cutting boundaries
                            that already partition the population would be change
                            for its own sake. NOT re-derived.
      published ceilings    WRONG, and wrong before Phase 4 — but indexed on the
                            wrong DIMENSION rather than mis-valued. See
                            test_the_published_ceiling_is_indexed_on_the_pathway.
      supply chain          the real finding. Two thirds of revived runs ended
      transparency          pinned at a clamp. Recalibrated; this module pins the
                            result.

WHY CALIBRATION IS VERSIONED
    A switch decides whether a mechanic runs. A knob decides what it is worth, and
    it is just as capable of re-grading a finished session — more so, because
    changing a global constant does it silently and to everyone at once. So a rule
    set carries its numbers as well as its switches, and the compatibility
    guarantee covers both halves.
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("USE_MEMORY_DB", "true")

import golden_matrix_harness as H       # noqa: E402
import rules as R                       # noqa: E402
import stress_harness as S              # noqa: E402
from terminal_valuation import (        # noqa: E402
    MR_CEILING, MR_PUBLISHED_CEILINGS, PATHWAY_MR_HEADROOM,
    max_achievable_mr_for, _THRESHOLDS,
)

# A CI-sized sample. The numbers in the docstring come from 3,300 pairs run
# offline and recorded in docs/verification/phase5_recalibration.md; this many is
# enough to catch a regression that moves a distribution, and cheap enough to run
# on every commit.
_N = 60
_SEED = 5150


@pytest.fixture(scope="module")
def sample():
    return S.paired(_N, _SEED, swans=False)


# ═══════════════════════════════════════════════════════════════════
#  THE KNOB LAYER
# ═══════════════════════════════════════════════════════════════════

def test_a_knob_is_versioned_like_a_switch():
    assert R.rule_value({}, "sct_entropy_per_round") == -3.0, (
        "the BASELINE entropy has moved; that re-grades every session played "
        "under 2026.09")
    assert R.rule_value({R.RULES_FLAG: "2026.10"}, "sct_entropy_per_round") == -1.0


def test_an_unknown_knob_raises_and_so_does_a_ruleset_that_forgot_one():
    """Two failure modes, both loud. A typo'd knob name must not silently take a
    default, and a rule set that declares a switch but forgets its number must
    not silently borrow another version's."""
    with pytest.raises(R.UnknownKnob):
        R.rule_value({}, "sct_entropy_per_roundd")
    R.RULE_SETS["_probe_empty"] = R.RuleSet(
        version="_probe_empty", note="", switches=dict(R.RULE_SETS["2026.09"].switches))
    try:
        with pytest.raises(R.UnknownKnob):
            R.rule_value({R.RULES_FLAG: "_probe_empty"}, "sct_entropy_per_round")
    finally:
        R.RULE_SETS.pop("_probe_empty", None)


def test_every_knob_records_the_measurement_it_came_from():
    """A calibration constant with no recorded derivation is a number somebody
    liked. The rationale field is where the sweep that produced it lives."""
    for name, knob in R.KNOBS.items():
        assert knob.rationale.strip(), f"{name} has no rationale"
        assert any(ch.isdigit() for ch in knob.rationale), (
            f"{name}'s rationale cites no measurement")
        for version, ruleset in R.RULE_SETS.items():
            if version.startswith("_probe"):
                continue
            assert name in ruleset.calibration, f"{version} declares no {name}"


# ═══════════════════════════════════════════════════════════════════
#  THE RECALIBRATION
# ═══════════════════════════════════════════════════════════════════

def test_a_transparency_boost_applies_once_not_every_round():
    """The calibration error the revival exposed. The function applies its whole
    boost table EVERY round, which is invisible for the +5 the one working flag
    carries and ruinous for a +20: at that cadence a completed deep audit is a
    team commissioning the same audit ten times."""
    from systemic_risk_engine import calc_supply_chain_transparency as sct

    revived = {R.RULES_FLAG: "2026.10", "r1_flags": ["deep_audit_completed"]}
    score, diag = sct(30.0, revived, 2)
    assert diag["boosts_applied"] == {"deep_audit_completed": 20.0}
    assert score == pytest.approx(30.0 + 20.0 - 1.0)

    # Round two: same flag, already counted. Only the entropy applies.
    carried = dict(revived, supply_chain_transparency_diag=diag)
    score2, diag2 = sct(score, carried, 3)
    assert score2 == pytest.approx(score - 1.0), "the boost was applied twice"
    assert diag2["boosts_applied"] == {"deep_audit_completed": 20.0}, (
        "the applied-set must carry forward, or the boost re-applies next round")


def test_the_baseline_cadence_is_untouched():
    """2026.09 re-applies every round, and must keep doing so: materiality_aligned
    is a genuine top-level boolean, so its +5 has ALWAYS applied per round, and
    that is the behaviour every scored session carries."""
    from systemic_risk_engine import calc_supply_chain_transparency as sct
    flags = {"materiality_aligned": True}
    a, _ = sct(30.0, flags, 2)
    b, _ = sct(a, flags, 3)
    assert a == pytest.approx(32.0) and b == pytest.approx(34.0), (
        "the baseline no longer applies its boost every round")


def test_transparency_is_no_longer_pinned_at_a_clamp(sample):
    """THE PHASE 5 RESULT. Before recalibration, 66.9% of revived runs ended
    pinned at 0 or 100 — a score two thirds of teams could not move. After, 5.1%
    over the same 3,300 games, all at the floor and all having taken both negative
    flags."""
    revived = [b.sct for _a, b in sample]
    clamped = sum(1 for v in revived if v <= 0 or v >= 100)
    assert clamped / len(revived) < 0.20, (
        f"{clamped}/{len(revived)} revived runs end clamped. The offline sweep "
        "measured 5.1%; anything approaching the pre-recalibration 66.9% means "
        "the cadence or the entropy knob has regressed.")
    spread = {round(v / 10) * 10 for v in revived}
    assert len(spread) >= 4, (
        f"transparency only reaches {sorted(spread)} — a score with no middle is "
        "what the recalibration existed to fix")


def test_the_baseline_transparency_score_is_still_inert(sample):
    """An uncomfortable measurement worth keeping visible: under 2026.09 the
    transparency score is the SAME NUMBER in every game — no decision moves it,
    because the only boost whose flag a reader can see is materiality_aligned's
    +5. That is the state the revival exists to end, and it is also why the
    baseline fixtures show a monotone drift on every path."""
    baseline = {a.sct for a, _b in sample}
    assert len(baseline) <= 2, (
        f"the baseline transparency score now varies ({sorted(baseline)}); if a "
        "consumer was fixed without a rules version, the compatibility guarantee "
        "is broken")


# ═══════════════════════════════════════════════════════════════════
#  THE THREE CONSTANTS THAT DID NOT MOVE
# ═══════════════════════════════════════════════════════════════════

def test_the_clamp_is_a_safety_net_and_still_behaves_like_one(sample):
    """Measured over 3,300 pairs: 0.8% of runs clamp, under both rule sets. A
    clamp that bound routinely would be a scoring rule pretending to be a guard,
    and would need re-deriving; this one does not."""
    for label, outcomes in (("2026.09", [a for a, _ in sample]),
                            ("2026.10", [b for _, b in sample])):
        rate = sum(o.mr_ceiling_clamped for o in outcomes) / len(outcomes)
        assert rate < 0.10, (
            f"{label}: the 2.05 clamp now binds in {rate:.1%} of runs. It is "
            "documented as 10bp above the maximum; if it binds routinely it has "
            "become a scoring rule and needs re-deriving rather than defending.")
    assert MR_CEILING == 2.05


def test_the_archetype_thresholds_still_partition_the_population(sample):
    """Not re-derived, and the reason is a measurement rather than an omission:
    the population split moves by about a point between the rule sets. Boundaries
    that already separate the population should not be moved to look busy."""
    assert _THRESHOLDS == {"regenerative_titan": 1.8, "derisked_safe_haven": 1.2,
                           "fragile_giant": 0.8}
    for label, outcomes in (("2026.09", [a for a, _ in sample]),
                            ("2026.10", [b for _, b in sample])):
        counts = Counter(o.archetype for o in outcomes)
        assert len(counts) >= 3, (
            f"{label}: the thresholds now sort every team into {len(counts)} "
            f"bucket(s) ({dict(counts)}) — that IS a re-derivation trigger")
        biggest = counts.most_common(1)[0][1] / len(outcomes)
        assert biggest < 0.75, (
            f"{label}: {biggest:.0%} of teams land in one archetype; the "
            "boundaries have stopped discriminating")


def test_the_published_ceiling_is_indexed_on_the_pathway():
    """The one ceiling finding, and it predates Phase 4.

    MR_CEILING_BY_PARADIGM indexes on the paradigm. Measurement says the binding
    dimension is the ENDING PATHWAY: four of the five run an M_R calculator whose
    bonuses sit outside the 1.93 base sum. Observed pre-clamp maxima over 3,300
    games — climate_black_swan 2.2300, stakeholder_revolt 2.0800, against
    activist_ultimatum's 1.5800 — and 99 runs scored above the ceiling the
    facilitator panel published. That panel divides by this number to report
    mr_efficiency_pct, so a climate cohort could be shown over 100% efficiency.
    """
    assert max_achievable_mr_for({"ending_pathway": "activist_ultimatum"}) == \
        MR_PUBLISHED_CEILINGS["base"], (
        "the default pathway has no M_R calculator, so its ceiling is the base sum")
    for pathway in ("climate_black_swan", "stakeholder_revolt",
                    "regulatory_shutdown", "hostile_takeover"):
        ceiling = max_achievable_mr_for({"ending_pathway": pathway})
        assert ceiling == MR_CEILING, (
            f"{pathway} publishes {ceiling}; base + headroom exceeds the hard "
            "clamp, so the reachable ceiling IS the clamp")
    # …and no ceiling may ever exceed the clamp, whatever is added to the table.
    for pathway in PATHWAY_MR_HEADROOM:
        assert max_achievable_mr_for({"ending_pathway": pathway}) <= MR_CEILING


def test_no_sampled_game_beats_its_own_published_ceiling(sample):
    """The property the correction exists to restore. Before it, 99 of 3,300 runs
    scored above the number they were told was the maximum."""
    over = [(o.pathway, o.mr, max_achievable_mr_for({"ending_pathway": o.pathway}))
            for _a, o in sample
            if o.mr > max_achievable_mr_for({"ending_pathway": o.pathway}) + 1e-9]
    assert not over, f"{len(over)} run(s) scored above their published ceiling: {over[:5]}"


# ═══════════════════════════════════════════════════════════════════
#  THE STRESS HARNESS ITSELF
# ═══════════════════════════════════════════════════════════════════

def test_the_sample_is_reproducible():
    """A distribution nobody can regenerate is an anecdote."""
    one = S.sample_specs(8, seed=99)
    two = S.sample_specs(8, seed=99)
    assert [s.choices for s in one] == [s.choices for s in two]
    assert [s.seed_string for s in one] == [s.seed_string for s in two]
    assert [s.choices for s in S.sample_specs(8, seed=100)] != [s.choices for s in one]


def test_the_sample_spans_the_axes_it_claims_to(sample):
    """A sweep that quietly held a variable fixed would measure one game many
    times. Each axis has to actually vary."""
    assert len({o.pathway for a, o in sample}) >= 4, "the pathway axis is not varying"
    assert len({o.invest for a, o in sample}) >= 3, "the spend axis is not varying"
    assert len({o.capex for a, o in sample}) >= 3, "the capex axis is not varying"
    assert len({tuple(sorted(o.bonuses)) for a, o in sample}) >= 10, (
        "the sample reaches too few distinct premium combinations to describe a "
        "distribution")


def test_no_sampled_game_fails_to_run(sample):
    """A sweep that silently drops the games that crash biases the very
    distribution it exists to measure, so failures are recorded and asserted."""
    failures = [(a.label, a.failed or b.failed) for a, b in sample if a.failed or b.failed]
    assert not failures, f"{len(failures)} sampled game(s) failed: {failures[:3]}"
