"""flags/ — the typed boundary, proved equivalent to what it replaces.

A wrapper that is not faithful to collect_all_flags is worse than no wrapper:
it would silently change every flag-dependent number while looking like a
refactor. These tests exist to make that impossible, so the equivalence proofs
come first and the new behaviour second.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flag_utils import collect_all_flags, mr_flags_from   # noqa: E402
from flags import (                                            # noqa: E402
    FlagSet, UnknownFlag, REGISTRY, live, dead, inert, unverified,
)
from flags.registry import DEPRECATED, deprecated, revived_in   # noqa: E402
from flag_taxonomy import FLAG_TAXONOMY                   # noqa: E402
import golden_matrix_harness as H                         # noqa: E402


def _states():
    """Real end-states from every golden matrix path — the equivalence proofs
    run against states the engine actually produces, not hand-built dicts."""
    for name in sorted(H.PATHS):
        gs, _ = H.final_state(name)
        yield name, (gs.get("active_event_flags") or {})


# ═══════════════════════════════════════════════════════════════════
#  EQUIVALENCE — the wrapper must not change what is seen
# ═══════════════════════════════════════════════════════════════════

def test_from_state_matches_collect_all_flags_exactly():
    for name, aef in _states():
        assert FlagSet.from_flags(aef).names == frozenset(collect_all_flags(aef)), (
            f"FlagSet diverges from collect_all_flags on path '{name}'")


def test_as_mr_dict_matches_mr_flags_from_exactly():
    """The drop-in property. If this holds, calculate_mr's boundary can be
    migrated without touching a single number."""
    for name, aef in _states():
        assert FlagSet.from_flags(aef).as_mr_dict() == mr_flags_from(aef), (
            f"as_mr_dict diverges from mr_flags_from on path '{name}'")


def test_legacy_raw_reproduces_raw_dict_semantics():
    """Every declared flag reads the same through legacy_raw as through a bare
    .get() on the dict. This is what lets a known-wrong caller be migrated to
    the type WITHOUT changing behaviour, deferring the fix to Phase 4."""
    for name, aef in _states():
        lg = FlagSet.legacy_raw(aef)
        for flag in REGISTRY:
            assert lg.has(flag) == bool(aef.get(flag)), (
                f"legacy_raw disagrees with the raw dict for {flag!r} on '{name}'")


def test_the_two_constructors_actually_disagree():
    """Guards the premise. If these ever agree on real states, the defect this
    package exists for is gone and the package can be simplified."""
    disagreed = False
    for _, aef in _states():
        if FlagSet.from_flags(aef).names != FlagSet.legacy_raw(aef).names:
            disagreed = True
            break
    assert disagreed, (
        "from_state and legacy_raw now agree on every golden path; the "
        "list-vs-boolean storage split appears to have been fixed.")


# ═══════════════════════════════════════════════════════════════════
#  THE REGISTRY — held consistent with the tree in both directions
# ═══════════════════════════════════════════════════════════════════

def test_every_taxonomy_entry_is_registered_as_inert_or_deprecated():
    """DEPRECATED is a STRONGER ruling than the taxonomy's "deliberately unread",
    not a contradiction of it: the taxonomy says nobody reads this flag, and
    deprecation adds that nobody is ever going to. Phase 4 moved `spinoff` that
    way (remediation plan §4.2), so this direction of the invariant accepts
    either."""
    missing = sorted(set(FLAG_TAXONOMY) - set(REGISTRY))
    assert not missing, f"taxonomy entries absent from the registry: {missing}"
    allowed = {"INERT_BY_DESIGN", DEPRECATED}
    wrong = sorted(n for n in FLAG_TAXONOMY if REGISTRY[n].status not in allowed)
    assert not wrong, (
        f"flags ruled inert in flag_taxonomy.py but neither INERT_BY_DESIGN nor "
        f"DEPRECATED here: {wrong}")


def test_registry_and_declarations_agree():
    """Every name declared in a flags_set list has a registry entry."""
    declared = set()
    class D(ast.NodeVisitor):
        def visit_Dict(self, n):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "flags_set" \
                   and isinstance(v, (ast.List, ast.Tuple)):
                    for e in v.elts:
                        if isinstance(e, ast.Constant) and isinstance(e.value, str):
                            declared.add(e.value)
            self.generic_visit(n)
    skip = ("tests", "__pycache__", "manual_tests", "archive", ".git", "flags")
    for p in sorted(_BACKEND.rglob("*.py")):
        if any(s in p.parts for s in skip):
            continue
        try:
            D().visit(ast.parse(p.read_text(encoding="utf-8")))
        except SyntaxError:
            pass
    missing = sorted(declared - set(REGISTRY))
    assert not missing, (
        f"{len(missing)} declared flags have no registry entry: {missing[:10]}")


def test_the_registry_and_the_taxonomy_cannot_drift():
    """Both directions, so the two sources stay one source in effect.

    flag_taxonomy.py stays the owner-signed record and tests/test_flag_sweep.py
    keeps reading it; the registry carries the same rulings plus status, effect
    and evidence. Equality here is what makes that duplication safe.
    """
    from flag_taxonomy import FLAG_TAXONOMY as _tax
    ruled_unread = {s.name for s in inert()} | {s.name for s in deprecated()}
    assert ruled_unread >= set(_tax), (
        "flag_taxonomy.py rules a flag unread that the registry does not: "
        f"{sorted(set(_tax) - ruled_unread)}")
    # The other direction, minus the flags Phase 4 deprecated from a DEAD_DEFECT
    # ruling rather than from a taxonomy entry — those were never in the taxonomy
    # because the sweep counted their names as read.
    unaccounted = sorted({s.name for s in inert()} - set(_tax))
    assert not unaccounted, (
        f"the registry rules {unaccounted} INERT_BY_DESIGN and flag_taxonomy.py "
        "has no entry for them; the two sources have diverged")


def test_every_inert_flag_carries_a_ruling():
    unruled = sorted(s.name for s in inert() if not s.ruling)
    assert not unruled, f"INERT_BY_DESIGN with no ruling: {unruled[:10]}"


def test_registry_counts_are_stable():
    """A ratchet on the shape of the namespace. Moving means a flag was added,
    retired or reclassified, which should be a reviewed change."""
    assert len(REGISTRY) == 285, f"registry size moved: {len(REGISTRY)}"
    # 18/11/156 until 2026-09-08. Two reviewed movements since:
    #   Phase 3 moved hard_engineering LIVE -> DEAD_DEFECT. Phase 2 classified it
    #   by reading the code and following Appendix B; the probe ran it and found
    #   its only consumer reads the wrong generation of the flag bag
    #   (tests/test_flag_reachability.py proves it without the probe).
    #   Phase 4 introduced DEPRECATED and moved four flags there — resist_integrate,
    #   divest and green_bond_active from DEAD_DEFECT, spinoff from INERT_BY_DESIGN
    #   — because "nothing reads it" and "nothing is ever going to" are different
    #   rulings and the second one needs a removes_at.
    assert len(live()) == 17, f"LIVE count moved: {len(live())}"
    assert len(dead()) == 9, f"DEAD_DEFECT count moved: {len(dead())}"
    assert len(inert()) == 155, f"INERT count moved: {len(inert())}"
    assert len(deprecated()) == 4, f"DEPRECATED count moved: {len(deprecated())}"
    assert (len(live()) + len(dead()) + len(inert()) + len(unverified())
            + len(deprecated())) == len(REGISTRY), "a flag has an unknown status"


# ═══════════════════════════════════════════════════════════════════
#  PHASE 2 — the registry may not claim more than it can show
# ═══════════════════════════════════════════════════════════════════

def test_every_live_flag_states_its_effect_and_cites_evidence():
    """LIVE is a claim about behaviour. A claim with no magnitude and no
    file:line is an opinion, and this registry is meant to settle arguments."""
    bad = [s.name for s in live() if not s.effect.strip() or not s.evidence.strip()]
    assert not bad, f"LIVE flags with no effect or no evidence: {bad}"


def test_every_dead_defect_cites_its_evidence():
    bad = [s.name for s in dead() if not s.effect.strip() or not s.evidence.strip()]
    assert not bad, f"DEAD_DEFECT flags with no explanation or evidence: {bad}"


def test_dead_defect_is_a_defect_register_not_a_ruling():
    """DEAD_DEFECT and INERT_BY_DESIGN must never overlap. One says the code is
    wrong; the other says the owner meant it. Conflating them is how a defect
    gets ruled away."""
    from flag_taxonomy import FLAG_TAXONOMY as _tax
    overlap = sorted(s.name for s in dead() if s.name in _tax)
    assert not overlap, (
        f"flags both ruled inert and recorded as defects: {overlap}. "
        "Decide which it is.")


def test_the_mislabelled_flags_are_now_correct():
    """The Phase 2 finding, pinned, plus the one Phase 3 added.

    The first eleven were LIVE in the first cut of the registry because LIVE meant
    'absent from flag_taxonomy.py', and the taxonomy is built from a sweep that
    counts a quoted occurrence as a read. Each was verified dead at 0ad1246.

    hard_engineering joined them on 2026-09-08. It survived the Phase 2 pass
    because that pass read the code and Appendix B, and both attribute the R5
    resilience factor to the flag — impact_engine.py:93 takes it from the chosen
    option's impacts dict instead, and the flag's only real consumer reads the
    post-tick flag bag, which never holds r5_flags. Twelve now, and the twelfth was
    found by running the engine rather than reading it.
    """
    # green_bond_active, resist_integrate and divest left this set at Phase 4 —
    # not because anything changed about them, but because DEPRECATED says what
    # DEAD_DEFECT could not: no consumer is coming.
    expected = {
        "supply_chain_disruption_risk", "remediation_active",
        "circular_redesign", "epr_program", "waste_to_energy", "water_efficiency_all",
        "desalination_built", "immediate_closure", "hard_engineering",
    }
    assert {s.name for s in dead()} == expected


# ═══════════════════════════════════════════════════════════════════
#  PHASE 4 — deprecation and revival, as registry facts
# ═══════════════════════════════════════════════════════════════════

def test_every_deprecated_flag_names_the_release_that_deletes_it():
    """Deprecation without a removal date is just a stronger adjective. The point
    of the field is that the deletion is scheduled and someone has to either do
    it or argue against it."""
    undated = sorted(s.name for s in deprecated() if not s.removes_at)
    assert not undated, f"DEPRECATED with no removes_at: {undated}"
    unruled = sorted(s.name for s in deprecated() if not s.ruling.strip())
    assert not unruled, f"DEPRECATED with no ruling: {unruled}"


def test_a_deprecated_flag_is_still_declared():
    """Deprecation is NOT deletion, and that distinction is the whole point:
    dropping a declared flag while cohorts are in flight changes what a replayed
    session's r{N}_flags contains even when no number moves. The flag stays in
    the config until its removes_at release."""
    from round_configs import get_round_config
    declared = {f for r in range(1, 11)
                for opt in (get_round_config(r).get("options") or {}).values()
                for f in (opt.get("flags_set") or [])}
    for spec in deprecated():
        if "round_configs.py" in spec.declared_in:
            assert spec.name in declared, (
                f"{spec.name} is DEPRECATED and has already been deleted from "
                "round_configs; deprecation was supposed to keep it declared until "
                f"{spec.removes_at}")


def test_the_revived_flags_agree_with_the_rules_module():
    """revived_in is the Phase 5 cut-over filter, so it has to name a rules
    version that exists and to agree with what the reachability probe measures."""
    import rules as R
    for spec in REGISTRY.values():
        if spec.revived_in:
            assert spec.revived_in in R.RULE_SETS, (
                f"{spec.name}.revived_in={spec.revived_in!r} is not a declared "
                f"rule set: {sorted(R.RULE_SETS)}")
            assert spec.status == "DEAD_DEFECT", (
                f"{spec.name} carries revived_in but is {spec.status}; while "
                "rules.CURRENT_VERSION predates the revival the flag IS dead for "
                "every session, and the registry should say so")
    assert {s.name for s in revived_in("2026.10")} == {
        "supply_chain_disruption_risk", "remediation_active", "epr_program",
        "circular_redesign", "hard_engineering",
    }, "the revived set has moved; tests/test_flag_reachability.py is the arbiter"


def test_no_flag_is_both_revived_and_deprecated():
    """A flag cannot be scheduled for deletion and for repair at the same time.
    If it ever is, someone has made two decisions about it in two places."""
    both = sorted(s.name for s in REGISTRY.values() if s.revived_in and s.removes_at)
    assert not both, f"scheduled for both revival and removal: {both}"


def test_unverified_only_ever_shrinks():
    """The ratchet Phase 3 exists to drive down.

    UNVERIFIED means reachability has not been established either way. Adding to
    it means a flag was declared without being traced; that is allowed, but it
    must be a deliberate, visible change rather than drift.
    """
    assert len(unverified()) <= 100, (
        f"UNVERIFIED grew to {len(unverified())} (was 100). A newly declared flag "
        "needs a trace, or an explicit bump of this number with a reason.")


def test_no_flag_is_live_without_being_declared_somewhere():
    orphans = [s.name for s in live() if not s.declared_in]
    assert not orphans, f"LIVE but declared nowhere: {orphans}"


# ═══════════════════════════════════════════════════════════════════
#  STRICT MODE — and the defect it found on its first run
# ═══════════════════════════════════════════════════════════════════

def test_strict_mode_rejects_an_unregistered_name():
    fs = FlagSet.from_flags({}, strict=True)
    with pytest.raises(UnknownFlag):
        fs.has("no_such_flag_anywhere")
    assert fs.has("community_fund") is False   # registered, absent, no raise


def test_deep_audit_is_read_but_never_written():
    """A real defect, found by strict mode within minutes of the registry existing.

    ceo_interview.py reads "deep_audit" at :197, :316 and :811 to award
    ethical-reasoning credit. Nothing anywhere writes it. The flag Round 1
    option B actually sets is "deep_audit_completed". So the credit can never
    be earned.

    Pinned rather than fixed: correcting the name turns a dormant branch on,
    which is a behaviour change and belongs in Phase 4 behind a rules version.
    When it is fixed, this test fails and should be deleted.
    """
    assert REGISTRY.get("deep_audit") is None, (
        "'deep_audit' is now registered — if it gained a writer, delete this test")
    assert REGISTRY.get("deep_audit_completed") is not None, \
        "the correctly-named flag should be registered"

    src = (_BACKEND / "ceo_interview.py").read_text(encoding="utf-8")
    assert '"deep_audit"' in src, "ceo_interview.py no longer reads the wrong name"
