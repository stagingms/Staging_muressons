"""Every declared flag is read, or carries a ruling — and rulings cannot rot.

DEEP-5/9 (owner rulings 2026-09-01). The pre-repair failure class: a config
declares a flag in `flags_set`, the narrative promises a consequence, and no
mechanic ever reads it (F-7/B-4 at scale — 117 of 263 declared flags at the
time of the ruling). Rather than wiring 117 flags blindly or deleting stored
state, each unread flag carries an explicit classification in
backend/flag_taxonomy.py. This test holds that line in BOTH directions:

  1. A NEW declared flag with no reader and no taxonomy entry fails — you
     cannot add a promised-but-unmodelled consequence silently.
  2. A taxonomy entry for a flag that GAINED a reader fails — the registry
     must shrink when reality improves.
  3. A taxonomy entry for a flag nobody declares any more fails — no stale
     rulings.

Read detection is intentionally coarse (any quoted occurrence of the flag
string outside a flags_set list, in backend non-test code or frontend/src):
false "read" positives are cheap (the flag just isn't required to carry an
entry), false negatives are what the taxonomy exists to adjudicate.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from flag_taxonomy import FLAG_TAXONOMY  # noqa: E402

FRONTEND_SRC = BACKEND.parent / "frontend" / "src"

# Files whose mention of a flag string is never a "read": the registry itself,
# this test, and every test file.
_EXCLUDED_PARTS = ("tests", "__pycache__", ".git")
_EXCLUDED_NAMES = ("flag_taxonomy.py",)


def _backend_sources() -> dict[str, str]:
    out = {}
    for p in BACKEND.rglob("*.py"):
        rel = p.relative_to(BACKEND)
        if any(part in _EXCLUDED_PARTS for part in rel.parts):
            continue
        if rel.name in _EXCLUDED_NAMES:
            continue
        out[str(rel)] = p.read_text(encoding="utf-8", errors="replace")
    return out


def _frontend_sources() -> dict[str, str]:
    out = {}
    if FRONTEND_SRC.exists():
        for p in FRONTEND_SRC.rglob("*"):
            if p.suffix in (".ts", ".tsx", ".js", ".jsx") and "node_modules" not in p.parts:
                out[str(p)] = p.read_text(encoding="utf-8", errors="replace")
    return out


class _FlagsSetCollector(ast.NodeVisitor):
    def __init__(self):
        self.declared: dict[str, set] = {}
        self._file = ""

    def collect(self, fname: str, text: str) -> None:
        self._file = fname
        try:
            self.visit(ast.parse(text))
        except SyntaxError:
            pass

    def visit_Dict(self, node: ast.Dict) -> None:
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value == "flags_set":
                if isinstance(v, (ast.List, ast.Tuple)):
                    for elt in v.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            self.declared.setdefault(elt.value, set()).add(self._file)
        self.generic_visit(node)


def _declaration_occurrences(text: str, flag: str) -> int:
    """Occurrences of the quoted flag that sit inside a flags_set list."""
    n = 0
    for m in re.finditer(re.escape(json.dumps(flag)), text):
        chunk = text[max(0, m.start() - 400):m.start()]
        idx = chunk.rfind("flags_set")
        if idx != -1 and idx > chunk.rfind("]"):
            n += 1
    return n


def _sweep():
    be = _backend_sources()
    fe = _frontend_sources()
    collector = _FlagsSetCollector()
    for fname, text in be.items():
        collector.collect(fname, text)
    declared = collector.declared

    read, unread = set(), set()
    for flag in declared:
        quoted = re.compile(r"[\"']" + re.escape(flag) + r"[\"']")
        is_read = any(quoted.search(t) for t in fe.values())
        if not is_read:
            for text in be.values():
                total = len(quoted.findall(text))
                if total and total > _declaration_occurrences(text, flag):
                    is_read = True
                    break
        (read if is_read else unread).add(flag)
    return declared, read, unread


_DECLARED, _READ, _UNREAD = _sweep()


def test_the_sweep_still_sees_the_surface():
    """Guards the sweep itself: if config loading or the AST walk breaks, the
    other tests would pass vacuously on an empty set."""
    assert len(_DECLARED) > 200, f"only {len(_DECLARED)} declared flags found — sweep broken?"
    assert _UNREAD, "zero unread flags — either the millennium arrived or the sweep broke"


def test_every_unread_declared_flag_carries_a_ruling():
    missing = sorted(_UNREAD - set(FLAG_TAXONOMY))
    assert not missing, (
        f"{len(missing)} declared flag(s) have no reader and no taxonomy ruling: "
        f"{missing[:10]}{' …' if len(missing) > 10 else ''}\n"
        "Wire a reader, or add an entry to backend/flag_taxonomy.py with the owner's ruling."
    )


def test_no_taxonomy_entry_for_a_flag_that_is_now_read():
    stale = sorted(set(FLAG_TAXONOMY) & _READ)
    assert not stale, (
        f"taxonomy entries exist for flag(s) that now HAVE a reader: {stale[:10]}\n"
        "Reality improved — delete these entries from backend/flag_taxonomy.py."
    )


def test_no_taxonomy_entry_for_an_undeclared_flag():
    ghosts = sorted(set(FLAG_TAXONOMY) - set(_DECLARED))
    assert not ghosts, (
        f"taxonomy entries exist for flag(s) nobody declares: {ghosts[:10]}\n"
        "Stale ruling — delete these entries from backend/flag_taxonomy.py."
    )
