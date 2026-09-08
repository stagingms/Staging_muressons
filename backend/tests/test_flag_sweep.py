"""Every declared flag is read, or carries a ruling — and the sweep can see.

Replaces tests/test_flag_taxonomy.py (FLAG-11, audit 2026-09-04, WP-24), which
was green while blind:
  • files with a UTF-8 BOM were skipped (`except SyntaxError: pass`) — the
    ethics side track's 24 `es_*` flags never entered the declared set;
  • a pillar OPTION KEY (`"microgrids": {`) counted as a READ of the flag
    `microgrids` — 31 unread core-config flags escaped a ruling that way;
  • the frontend half swept `frontend/src`, which does not exist.

Invariants (DEEP-5/9, owner rulings 2026-09-01):
  1. a declared flag with no reader and no taxonomy entry fails;
  2. a taxonomy entry for a flag that gained a reader fails;
  3. a taxonomy entry for a flag nobody declares fails;
  4. RATCHET — the number of flags declared in the four core config files
     (pillar_configs, round_configs, healthcare_configs, round2_csrd) that
     have no reader and no ruling is 0 and must stay 0.

"Read" = a quoted occurrence of the flag outside its flags_set declaration
that is not a config option key and not a comment, in backend non-test code
(the pillar→legacy proxy map counts: it routes the round handler) or in
frontend/app (tests excluded).
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from flag_taxonomy import FLAG_TAXONOMY  # noqa: E402

FRONTEND_APP = BACKEND.parent / "frontend" / "app"
CORE_CONFIG_FILES = {"pillar_configs.py", "round_configs.py", "healthcare_configs.py", "round2_csrd.py"}

# `flags/` is excluded for the same reason flag_taxonomy.py is: it is a
# SPECIFICATION of the namespace, not a consumer of it. flags/registry.py quotes
# every flag name by construction, and flags/flagset.py names several in its
# docstring, so without this the sweep marks all 285 flags read and _UNREAD
# collapses to the empty set — the sweep would go green by describing the
# problem rather than by anyone fixing it.
_EXCLUDED_PARTS = ("tests", "__pycache__", ".git", "manual_tests", "db", "flags")
_EXCLUDED_NAMES = ("flag_taxonomy.py",)


def _backend_sources() -> dict[str, str]:
    out = {}
    for p in sorted(BACKEND.rglob("*.py")):
        rel = p.relative_to(BACKEND)
        if any(part in _EXCLUDED_PARTS for part in rel.parts) or rel.name in _EXCLUDED_NAMES:
            continue
        out[str(rel)] = p.read_text(encoding="utf-8-sig", errors="replace")   # BOM-safe (FLAG-11)
    return out


def _frontend_sources() -> dict[str, str]:
    out = {}
    if FRONTEND_APP.exists():
        for p in sorted(FRONTEND_APP.rglob("*")):
            if p.suffix in (".ts", ".tsx", ".js", ".jsx") and "node_modules" not in p.parts \
                    and "__tests__" not in p.parts:
                out[str(p.relative_to(FRONTEND_APP))] = p.read_text(encoding="utf-8-sig", errors="replace")
    return out


class _FlagsSetCollector(ast.NodeVisitor):
    def __init__(self):
        self.declared: dict[str, set] = {}
        self.decl_lines: set[tuple[str, int]] = set()
        self._file = ""

    def collect(self, fname: str, text: str) -> None:
        self._file = fname
        self.visit(ast.parse(text))   # a SyntaxError is a real failure, not a skip

    def visit_Dict(self, node: ast.Dict) -> None:
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value == "flags_set" and isinstance(v, (ast.List, ast.Tuple)):
                for elt in v.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        self.declared.setdefault(elt.value, set()).add(self._file)
                        self.decl_lines.add((self._file, elt.lineno))
        self.generic_visit(node)


def _sweep():
    be = _backend_sources()
    fe = _frontend_sources()
    collector = _FlagsSetCollector()
    for fname, text in be.items():
        collector.collect(fname, text)
    declared = collector.declared
    decl_lines = collector.decl_lines

    def _is_read_line(fname: str, lineno: int, line: str, flag: str) -> bool:
        if (fname, lineno) in decl_lines or "flags_set" in line:
            return False
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            return False
        if fname in CORE_CONFIG_FILES and re.match(r'^["\']' + re.escape(flag) + r'["\']\s*:\s*\{', stripped):
            return False   # a config OPTION KEY, not a read of the flag (FLAG-11)
        return True

    read, unread, core_inert = set(), set(), set()
    for flag in declared:
        quoted = re.compile(r"[\"']" + re.escape(flag) + r"[\"']")
        is_read = False
        for fname, text in be.items():
            for i, line in enumerate(text.splitlines(), 1):
                if quoted.search(line) and _is_read_line(fname, i, line, flag):
                    is_read = True
                    break
            if is_read:
                break
        if not is_read:
            is_read = any(quoted.search(t) for t in fe.values())
        (read if is_read else unread).add(flag)
        if not is_read and declared[flag] & CORE_CONFIG_FILES:
            core_inert.add(flag)
    return declared, read, unread, core_inert


_DECLARED, _READ, _UNREAD, _CORE_INERT = _sweep()


def test_the_sweep_still_sees_the_surface():
    """Guards the sweep itself: if config loading or the AST walk breaks, the
    other tests would pass vacuously on an empty set."""
    assert len(_DECLARED) > 250, f"only {len(_DECLARED)} declared flags found — sweep broken?"
    assert any(f.startswith("es_") for f in _DECLARED), "the BOM-prefixed ethics track is invisible again (FLAG-11)"
    assert _UNREAD, "zero unread flags — either the millennium arrived or the sweep broke"
    assert FRONTEND_APP.exists(), "frontend/app not found — the frontend half of the sweep is a no-op"


def test_every_unread_declared_flag_carries_a_ruling():
    missing = sorted(_UNREAD - set(FLAG_TAXONOMY))
    assert not missing, (
        f"{len(missing)} declared flag(s) have no reader and no taxonomy ruling: "
        f"{missing[:12]}{' …' if len(missing) > 12 else ''}\n"
        "Wire a reader, or add an entry to backend/flag_taxonomy.py with the owner's ruling."
    )


def test_no_taxonomy_entry_for_a_flag_that_is_now_read():
    stale = sorted(set(FLAG_TAXONOMY) & _READ)
    assert not stale, (
        f"taxonomy entries exist for flag(s) that now HAVE a reader: {stale[:12]}\n"
        "Reality improved — delete these entries from backend/flag_taxonomy.py."
    )


def test_no_taxonomy_entry_for_an_undeclared_flag():
    ghosts = sorted(set(FLAG_TAXONOMY) - set(_DECLARED))
    assert not ghosts, (
        f"taxonomy entries exist for flag(s) nobody declares: {ghosts[:12]}\n"
        "Stale ruling — delete these entries from backend/flag_taxonomy.py."
    )


def test_ratchet_no_unruled_inert_flag_in_the_core_configs():
    """FLAG-11 ratchet: 31 core-config flags were inert and unruled at the audit
    (masked by the option-key false positive). Zero, and it stays zero."""
    unruled = sorted(_CORE_INERT - set(FLAG_TAXONOMY))
    assert not unruled, (
        f"{len(unruled)} inert core-config flag(s) without a ruling: {unruled}\n"
        "An option promises a consequence nothing models. Wire it or rule it."
    )
