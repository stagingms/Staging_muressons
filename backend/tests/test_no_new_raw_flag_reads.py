"""No NEW raw reads of a declared flag. The lint half of Phase 1.

WHY A BASELINE RATHER THAN A BAN
    47 raw flag reads exist today, in 10 files. Banning them outright would fail
    the build on day one and be switched off by the second person to hit it. So
    the rule is a ratchet: the existing set is frozen, a new one fails, and a
    removed one ALSO fails — with a message saying to shrink the baseline. The
    list only goes down.

WHAT COUNTS AS A RAW READ
    A read-by-name of a REGISTERED flag off a flag-bag expression:
        flags.get("community_fund")
        "community_fund" in flags
        flags["community_fund"]
    Reads of state or configuration living in the same dict — difficulty_tier,
    caroic, terminal_value and the other 111 non-flag keys — are NOT in scope.
    That distinction is the whole reason this rule is enforceable: active_event_flags
    carries 136 distinct keys and only 25 of them are flags.

WHAT IT DOES NOT CLAIM
    A site on this list is not necessarily a bug. Most read an already-collected
    set and are correct; they are listed because they are untyped, not because
    they are wrong. The list is a migration ledger, not a defect register.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

from flags import REGISTRY  # noqa: E402

_SKIP_PARTS = ("tests", "__pycache__", "manual_tests", "archive", ".git", "flags")
_FLAG_VARS = {"flags", "aef", "active_event_flags", "event_flags", "all_flags",
              "prev_flags", "previous_flags", "merged_flags", "cur_flags",
              # Widened 2026-09-08. Phase 4 named some flag bags differently and
              # the detector lost sight of reads it had been counting —
              # engine.py's deep_audit_completed test moved from
              # `current_global.get("active_event_flags", {})` to a local
              # `_fog_flags` and simply vanished from this list, which would have
              # read as PROGRESS. A detector that goes blind when a variable is
              # renamed is worse than no detector, because its silence is
              # indistinguishable from success.
              "_fog_flags", "_bio_flags", "main_flags"}


def _is_flag_bag(node: ast.AST) -> bool:
    if isinstance(node, ast.Name) and node.id in _FLAG_VARS:
        return True
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
       and node.slice.value == "active_event_flags":
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
       and node.func.attr in ("get", "setdefault") and node.args \
       and isinstance(node.args[0], ast.Constant) \
       and node.args[0].value == "active_event_flags":
        return True
    return False


class _Reads(ast.NodeVisitor):
    def __init__(self, rel: str):
        self.rel = rel
        self.hits: set[tuple[str, str]] = set()

    def _note(self, key):
        if key in REGISTRY:
            self.hits.add((self.rel, key))

    def visit_Call(self, n):
        if isinstance(n.func, ast.Attribute) and n.func.attr == "get" \
           and _is_flag_bag(n.func.value) and n.args \
           and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
            self._note(n.args[0].value)
        self.generic_visit(n)

    def visit_Compare(self, n):
        if len(n.ops) == 1 and isinstance(n.ops[0], (ast.In, ast.NotIn)) \
           and isinstance(n.left, ast.Constant) and isinstance(n.left.value, str) \
           and _is_flag_bag(n.comparators[0]):
            self._note(n.left.value)
        self.generic_visit(n)

    def visit_Subscript(self, n):
        if _is_flag_bag(n.value) and isinstance(n.slice, ast.Constant) \
           and isinstance(n.slice.value, str) and not isinstance(getattr(n, "ctx", None), ast.Store):
            self._note(n.slice.value)
        self.generic_visit(n)


def _current() -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for p in sorted(_BACKEND.rglob("*.py")):
        if any(s in p.parts for s in _SKIP_PARTS):
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        v = _Reads(str(p.relative_to(_BACKEND)))
        v.visit(tree)
        found |= v.hits
    return found


# Frozen 2026-09-08 against commit 0ad1246. (file, flag) pairs rather than line
# numbers, so unrelated edits do not churn the list.
_BASELINE: set[tuple[str, str]] = {
    ("admin_router.py", "ai_monetised"),
    ("admin_router.py", "brsr_greenwash_risk"),
    ("admin_router.py", "brsr_pioneer"),
    ("admin_router.py", "governance_fragility"),
    ("ceo_interview.py", "community_fund"),
    # Phase 4, 2026-09-08. NOT a new read: this line already existed as
    # `all_flags.get("deep_audit")`, a name no configuration anywhere declares —
    # so the detector, which only knows registered names, could not see it. The
    # rename to the real flag made a pre-existing raw read VISIBLE rather than
    # adding one. All four ceo_interview reads now go through _flag_view, which is
    # the boundary this detector wants; they stay listed because the 2026.09
    # branch of that view deliberately preserves the raw read.
    ("ceo_interview.py", "deep_audit_completed"),
    ("ceo_interview.py", "ethical_ai_overhaul"),
    ("ceo_interview.py", "managed_transition"),
    # Newly VISIBLE, not newly written: `main_flags` was not in _FLAG_VARS until
    # 2026-09-08, so these two reads in the supply-chain side track have always
    # been here and this list simply could not see them. Both are the 2026.09
    # branch of a rule-gated read (side_tracks/supply_chain/track.py), preserved
    # deliberately, so they belong on the ledger rather than being "fixed" away.
    ("side_tracks/supply_chain/track.py", "blockchain_traceability"),
    ("side_tracks/supply_chain/track.py", "deep_audit_completed"),
    ("ending_pathways.py", "early_decarboniser"),
    ("ending_pathways.py", "full_remediation"),
    ("ending_pathways.py", "governance_fragility"),
    ("ending_pathways.py", "nature_based_resilience"),
    ("ending_pathways.py", "scope_3_transparency"),
    ("engine.py", "deep_audit_completed"),
    ("pedagogical_engine.py", "early_decarboniser"),
    ("pedagogical_engine.py", "electronics_blindspot"),
    ("pedagogical_engine.py", "insurance_only"),
    ("round_logic.py", "ai_monetised"),
    ("round_logic.py", "blockchain_traceability"),
    ("round_logic.py", "brsr_net_positive_dividend"),
    ("round_logic.py", "community_fund"),
    ("round_logic.py", "compliance_gap"),
    ("round_logic.py", "deferred_audit"),
    ("round_logic.py", "early_decarboniser"),
    ("round_logic.py", "electronics_blindspot"),
    ("round_logic.py", "hard_engineering"),
    ("round_logic.py", "managed_transition"),
    ("round_logic.py", "outsource_opacity"),
    ("round_logic.py", "waste_compliance_gap"),
    ("shadow_board_audit.py", "governance_fragility"),
    ("side_tracks/corporate_sdg/track.py", "greenwash_risk"),
    ("side_tracks/ethics_sustainability/track.py", "deep_audit_completed"),
    ("terminal_valuation.py", "brsr_net_positive_dividend"),
    ("terminal_valuation.py", "civil_water_priority"),
    ("terminal_valuation.py", "community_fund"),
    ("terminal_valuation.py", "electronics_water_priority"),
    ("terminal_valuation.py", "ethical_ai_overhaul"),
    ("terminal_valuation.py", "insurance_only"),
    ("terminal_valuation.py", "managed_transition"),
    ("terminal_valuation.py", "synergy_unlock"),
}


def test_no_new_raw_flag_reads():
    added = sorted(_current() - _BASELINE)
    assert not added, (
        f"{len(added)} new raw flag read(s):\n  "
        + "\n  ".join(f"{f}: {k}" for f, k in added)
        + "\n\nConstruct a FlagSet at the boundary instead:\n"
        "    from flags import FlagSet\n"
        "    fs = FlagSet.from_state(global_state)   # expands the rN_flags lists\n"
        "    fs = FlagSet.legacy_raw(flags)          # only to preserve a known-wrong read\n"
    )


def test_the_baseline_shrinks_and_never_silently_grows():
    removed = sorted(_BASELINE - _current())
    assert not removed, (
        f"{len(removed)} baselined read(s) are gone — good. Delete them from "
        f"_BASELINE in this file:\n  " + "\n  ".join(f"{f}: {k}" for f, k in removed))


def test_the_rule_is_scoped_to_flags_not_to_the_whole_state_bag():
    """Guards the scope decision. active_event_flags also carries scalar state
    and session config; those reads are deliberately out of scope, and if the
    registry ever swallowed them this rule would become unenforceable."""
    for key in ("difficulty_tier", "stochastic_seed", "terminal_value",
                "regenerative_multiple", "caroic", "workforce_readiness"):
        assert key not in REGISTRY, (
            f"{key!r} is state, not a flag, and must not be in the flag registry")
