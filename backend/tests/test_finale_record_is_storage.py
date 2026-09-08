"""The R10 finale's re-run record is storage, not a flag.

THE DEFECT
    round_logic._stamp_finale_valuation has to be re-runnable on the CLOSING
    state (audit F-08 / SEAM-05): the finale runs inside post_tick, BEFORE the
    round's NPC fines, agent hits and R10 balance sheet land, so
    router.commit_turn re-runs its valuation stamps afterwards. To make that
    replay exact, the R10 handler records the inputs it resolved — including
    `all_flags`, a snapshot of every flag in force at R10, and `special`, the
    pathway's config dict.

    That record was parked in `active_event_flags` under a bare key. But
    active_event_flags IS the flag namespace, and flag_utils.collect_all_flags
    recurses into any nested dict whose key is not underscore-prefixed and
    harvests every list under a key containing "flag". So the record handed the
    whole game's flag history — plus `is_healthcare`, `brsr` and every boolean
    inside the pathway config — back to any consumer that asked the R10 events
    bag what was set THIS round.

    Measured in Phase 5 on path all_c under rules 2026.10:

        R2   detect_betrayal -> materiality_ignored   (set at R2)
        R4   detect_betrayal -> deny_and_deflect      (set at R4)
        R10  detect_betrayal -> BOTH, via the record

    One R4 decision, two trust scars. That third fire was the largest single
    grading change in the whole flag remediation, and it was not a mechanic —
    it was a storage key that did not follow the namespace's own convention.

WHY THESE TESTS AND NOT A SWITCH
    Every other behaviour change in this remediation is versioned, because each
    restores a mechanic that scored sessions were played without. This one is
    not, because it has no expression under 2026.09: measured across all seven
    golden paths, moving the record under the private prefix left every graded
    quantity identical (M_R, terminal value, escalations, the finale stamps,
    every global/score/bus figure) and moved only the diagnostic listing of
    what a correct reader sees at R10 — from which six names disappeared, one a
    config key and five transient markers the round had already cleared.
    docs/verification/phase5_recalibration.md carries the measurement.

    The convention itself is not new. flag_utils:30-35 already states it, for
    `_materiality_idempotency`, with the same rationale in the same words:
    private state bags are storage, and recursing into them "polluted the flag
    namespace with names no writer ever intended as flags." This record simply
    did not follow it.
"""
from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

import golden_matrix_harness as H
from flag_utils import (FINALE_INPUTS_KEY, FINALE_INPUTS_LEGACY_KEY,
                        collect_all_flags, finale_inputs_of)


# ── the reader, on its own ────────────────────────────────────────────────
def test_the_reader_accepts_a_record_persisted_under_the_old_key():
    """Replay compatibility. Sessions were persisted with the bare key, and
    restamp_finale_valuation must still find their record — otherwise every
    stored game silently stops restamping and its closing numbers revert to the
    mid-pipeline snapshot the F-08 audit was raised about."""
    legacy = {FINALE_INPUTS_LEGACY_KEY: {"brsr": True, "choice": "option_a"}}
    assert finale_inputs_of(legacy) == {"brsr": True, "choice": "option_a"}


def test_the_reader_prefers_the_current_key_and_falls_through_bags():
    current = {FINALE_INPUTS_KEY: {"choice": "new"},
               FINALE_INPUTS_LEGACY_KEY: {"choice": "old"}}
    assert finale_inputs_of(current) == {"choice": "new"}
    # extra first, then the persisted bag — the order restamp_finale_valuation uses
    assert finale_inputs_of({}, current) == {"choice": "new"}
    assert finale_inputs_of(None, {}, {"x": 1}) == {}


def test_an_empty_record_reads_as_no_finale():
    """router.commit_turn gates the restamp on this being falsy. A record that
    is present but empty means the finale did not run."""
    assert finale_inputs_of({FINALE_INPUTS_KEY: {}}) == {}
    assert finale_inputs_of({FINALE_INPUTS_KEY: None}) == {}


def test_the_private_prefix_is_what_hides_the_record():
    """The mechanism, stated as a test so a rename cannot quietly undo it: the
    record is invisible to collect_all_flags only because of its prefix."""
    record = {"all_flags": ["deny_and_deflect"], "is_healthcare": True,
              "special": {"exit_multiple_ci_haircut": True}}
    assert collect_all_flags({FINALE_INPUTS_KEY: record}) == set()
    assert collect_all_flags({FINALE_INPUTS_LEGACY_KEY: record}) == {
        "deny_and_deflect", "is_healthcare", "exit_multiple_ci_haircut"}


# ── the writer, driven ────────────────────────────────────────────────────
@pytest.mark.parametrize("path_name", ["all_c", "adaptation"])
def test_the_finale_writes_its_record_under_the_private_key(path_name):
    _trace, gs, _bus = H.drive(path_name)
    bag = gs.get("active_event_flags") or {}
    assert FINALE_INPUTS_KEY in bag, "the R10 finale did not record its inputs"
    assert FINALE_INPUTS_LEGACY_KEY not in bag, (
        "the finale record is back in the flag namespace under a bare key")


@pytest.mark.parametrize("path_name", ["all_c", "distress_c", "adaptation", "regulatory"])
def test_the_record_contributes_no_flag_to_the_closing_bag(path_name):
    """The property that matters, on the four paths where it used to fail."""
    _trace, gs, _bus = H.drive(path_name)
    bag = gs.get("active_event_flags") or {}
    record = finale_inputs_of(bag)
    assert record, "no finale record to test against"
    without = collect_all_flags({k: v for k, v in bag.items()
                                 if k not in (FINALE_INPUTS_KEY, FINALE_INPUTS_LEGACY_KEY)})
    assert collect_all_flags(bag) == without, (
        "the finale record is contributing flag names to the closing bag: "
        f"{sorted(collect_all_flags(bag) - without)}")


def test_the_restamp_still_runs():
    """Moving the key must not break the gate it is read through. The finale's
    closing stamps only exist if restamp_finale_valuation was reached."""
    _trace, gs, _bus = H.drive("all_c")
    bag = gs.get("active_event_flags") or {}
    for stamp in ("terminal_value", "regenerative_multiple", "archetype",
                  "price_per_share", "exit_multiple_applied"):
        assert stamp in bag, f"the finale restamp did not run: {stamp} missing"


# ── the behaviour it was corrupting ───────────────────────────────────────
def test_one_decision_raises_one_betrayal(monkeypatch):
    """all_c takes deny_and_deflect exactly once, at R4 option_c. Under the
    revived reader the NPC and agent trust scars must fire in R4 and not again.

    Before the record moved, R10 raised a third betrayal on the same flag,
    because the record's `all_flags` snapshot made every historical flag look
    like it had just been set.
    """
    import npc_stakeholders as NS
    import autonomous_agents as AA

    seen: list[tuple[int, tuple[str, ...]]] = []
    state = {"round": 0}
    real = NS.detect_betrayal

    def spy(events):
        got = real(events)
        if got:
            from flag_utils import collect_all_flags as _c
            active = {k for k, v in (events or {}).items() if v is True} | _c(events or {})
            seen.append((state["round"], tuple(sorted(active & NS._BETRAYAL_FLAGS))))
        return got

    # The harness holds its own reference (`from round_logic import ...`), so the
    # round marker has to be attached where the call actually goes.
    real_engines = H.run_new_engines

    def engines(*a, **kw):
        state["round"] = int(kw.get("round_number") or 0)
        return real_engines(*a, **kw)

    monkeypatch.setattr(NS, "detect_betrayal", spy)
    monkeypatch.setattr(AA, "detect_betrayal", spy)
    monkeypatch.setattr(H, "run_new_engines", engines)

    H.drive("all_c", rules_version="2026.10")

    # Two consumers ask per round (npc_stakeholders and autonomous_agents), so
    # collapse to the distinct (round, flags) pairs.
    fires = sorted(set(seen))
    assert fires == [(2, ("materiality_ignored",)), (4, ("deny_and_deflect",))], (
        f"betrayal fired at {fires}; a flag is being detected outside the round "
        "it was set in")


def test_the_baseline_rule_set_is_untouched_by_the_move(monkeypatch):
    """2026.09 does not read option flags at all, so the record never reached
    detect_betrayal there. Pinned so the claim in this module's docstring — that
    the move needed no switch — stays true."""
    import npc_stakeholders as NS
    import autonomous_agents as AA

    seen: list[int] = []
    state = {"round": 0}
    real = NS.detect_betrayal
    real_engines = H.run_new_engines

    def spy(events):
        got = real(events)
        if got:
            seen.append(state["round"])
        return got

    def engines(*a, **kw):
        state["round"] = int(kw.get("round_number") or 0)
        return real_engines(*a, **kw)

    monkeypatch.setattr(NS, "detect_betrayal", spy)
    monkeypatch.setattr(AA, "detect_betrayal", spy)
    monkeypatch.setattr(H, "run_new_engines", engines)

    H.drive("all_c", rules_version="2026.09")
    assert sorted(set(seen)) == [2], (
        f"the baseline betrayal cadence moved: fired at rounds {sorted(set(seen))}")
