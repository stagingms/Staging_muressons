"""No containment tests over a STRINGIFIED container. The shape-E lint.

THE DEFECT THIS BANS
    Appendix B §B.13 names five shapes of broken flag read. Four of them fail
    CLOSED — the mechanic is simply absent, which is bad but inert. Shape E fails
    OPEN, and it was found in biodiversity_engine.py:442:

        audit_active = "deep_audit" in str(events.get("active_event_flags", {}))

    That asks whether eleven characters appear anywhere in the repr of a nested
    dictionary — keys, values, and the insides of nested dicts and lists alike —
    against a name no configuration declares. Measured across the golden matrix it
    is True at exactly three rounds and for three unrelated reasons: the repr of
    the r1_flags LIST at R1, the KEY `deep_audit_protected` (a different flag) at
    R4, and the insides of the `_finale_inputs` blob at R10.

WHY A LINT AND NOT JUST A FIX
    The fix is done (rules.SWITCHES["biodiversity_audit_gate_reads_flags"]). This
    exists because the pattern is invisible to BOTH existing guards, and so would
    the next instance be:

      * tests/test_flag_sweep.py cannot see it — the name in the test is not a
        declared flag, so the sweep has nothing to look for.
      * tests/flag_probe.py cannot see it — a substring test over a string is not
        a keyed read of any container, so no recording proxy is ever consulted.

    And the project has already been bitten by exactly this pattern once before,
    in an unrelated subsystem: main.py:681 carries the note that the old
    `"database_memory" in str(type(db))` detection "was DEAD". Two independent
    instances of one mistake is the definition of a thing worth banning.

WHAT IS ALLOWED
    Stringifying an EXCEPTION and matching on it is an ordinary, if fragile,
    idiom for reading a database driver's error text, and matching narrative
    patterns over deliberately stringified content is what situation_room does on
    purpose. Both are allow-listed by name below, and the allow-list is short
    precisely because the pattern is rare — which is what makes the ban cheap.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

_SKIP_PARTS = ("tests", "__pycache__", "manual_tests", "archive", ".git")

# (file, line-ish anchor) → why it is not a flag read. Anchors are the expression
# being stringified, so a MOVE does not break the test but a CHANGE does.
_ALLOWED: dict[str, set[str]] = {
    # A database driver's unique-constraint name, read out of the exception text.
    # Fragile, but it is an exception message and there is no structured
    # alternative in asyncpg.
    "router.py": {"exc"},
    # Deliberate: CRISIS_PATTERNS is matched over stringified narrative content,
    # which is the whole point of the function.
    "situation_room.py": {"f"},
    # The 2026.09 branch of the shape-E defect itself, preserved bug-for-bug
    # behind rules.SWITCHES["biodiversity_audit_gate_reads_flags"] because every
    # session played to date was scored under it. Delete this entry when the
    # baseline rule set retires.
    "biodiversity_engine.py": {"flags"},
}


def _unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:                                   # pragma: no cover
        return "<unparseable>"


class _Finder(ast.NodeVisitor):
    """`<something> in str(<expr>)` and its `not in` twin."""

    def __init__(self) -> None:
        self.hits: list[tuple[int, str, str]] = []

    def visit_Compare(self, node: ast.Compare) -> None:
        for op, comparator in zip(node.ops, node.comparators):
            if not isinstance(op, (ast.In, ast.NotIn)):
                continue
            # Walk down any .lower()/.strip()/.casefold() chain to the root
            # call: `x in str(flags).lower()` is the same defect wearing a hat,
            # and situation_room.py:51 is written exactly that way.
            root = comparator
            while isinstance(root, ast.Call) and isinstance(root.func, ast.Attribute):
                root = root.func.value
            if (isinstance(root, ast.Call)
                    and isinstance(root.func, ast.Name)
                    and root.func.id == "str"
                    and root.args):
                self.hits.append((node.lineno,
                                  _unparse(root.args[0]),
                                  _unparse(node)))
        self.generic_visit(node)


def _current() -> list[tuple[str, int, str, str]]:
    found = []
    for path in sorted(_BACKEND.rglob("*.py")):
        if any(part in path.parts for part in _SKIP_PARTS):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):       # pragma: no cover
            continue
        finder = _Finder()
        finder.visit(tree)
        for lineno, target, source in finder.hits:
            found.append((path.name, lineno, target, source))
    return found


def test_no_containment_test_over_a_stringified_container():
    """The ban. A new `x in str(y)` fails here unless y is allow-listed above."""
    offenders = [
        (name, lineno, target, source)
        for name, lineno, target, source in _current()
        if target not in _ALLOWED.get(name, set())
    ]
    assert not offenders, (
        f"{len(offenders)} containment test(s) over a stringified container:\n  "
        + "\n  ".join(f"{n}:{l}  {s}" for n, l, _t, s in offenders)
        + "\n\nAsk the container the question instead:\n"
          "    from flag_utils import collect_all_flags\n"
          '    if "deep_audit_completed" in collect_all_flags(flags): ...\n\n'
          "`x in str(container)` matches keys, values and the insides of nested "
          "dicts and lists alike, so it fires on things that merely CONTAIN the "
          "substring — it is the one defect shape in this codebase that fails "
          "OPEN. If the site is genuinely matching text (an exception message, "
          "narrative content), add the stringified expression to _ALLOWED with a "
          "reason."
    )


def test_the_allow_list_does_not_rot():
    """Every allow-listed entry must still exist. An entry for a site that has
    been deleted or rewritten is a licence nobody is using, and the next person
    to read it will assume the pattern is acceptable here."""
    present = {(name, target) for name, _l, target, _s in _current()}
    stale = sorted(
        f"{name}: {target}"
        for name, targets in _ALLOWED.items()
        for target in targets
        if (name, target) not in present
    )
    assert not stale, (
        "allow-list entries with no matching site — delete them:\n  "
        + "\n  ".join(stale))


def test_the_known_flag_layer_instance_is_still_gated():
    """The one real instance, held to its switch.

    biodiversity_engine's 2026.09 branch is allowed to keep the broken read; what
    is NOT allowed is for it to escape the rule set and become the only behaviour
    again. If the switch disappears, this fails.
    """
    import rules as R
    assert "biodiversity_audit_gate_reads_flags" in R.SWITCHES, (
        "the shape-E defect's switch is gone; either the 2026.09 branch was "
        "deleted (in which case remove it from _ALLOWED too) or the versioning "
        "was removed and the defect is unconditional again")
    source = (_BACKEND / "biodiversity_engine.py").read_text(encoding="utf-8")
    assert 'rule_on(flags, "biodiversity_audit_gate_reads_flags")' in source, (
        "biodiversity_engine no longer gates its audit read on the rule set")


def test_the_pattern_is_rare_enough_for_a_ban_to_be_cheap():
    """Guards the premise. This lint is affordable because there are four sites in
    the whole backend, three of them legitimate. If that ever stops being true the
    ban is the wrong instrument and someone should say so rather than growing the
    allow-list quietly."""
    total = len(_current())
    assert total <= 8, (
        f"{total} stringified-containment sites now exist. A ban with a large "
        "allow-list is a ban in name only — reconsider the approach.")
