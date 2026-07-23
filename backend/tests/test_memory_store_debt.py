"""Tripwire: the memory-store shortcut debt may only SHRINK.

An endpoint that imports database_memory directly bypasses the storage
abstraction. Under Postgres such code either reads a bootstrap cache or writes
into a dict the database never sees — a write that returns 200 and silently
persists nothing. This family shipped several production defects (pedagogical
settings, peer trends, player credentials) that memory-mode tests cannot catch.

The right long-term state is ZERO direct imports in endpoint modules, with all
access flowing through the injected `db` module's parity API. Until that
refactor lands, this test pins the CURRENT count per file: removing a shortcut
lowers the ceiling (update the number downward); adding one FAILS CI.

If this test just failed on your new code: use `db.<api>` (fetch_all_sessions,
get_session_info, update_session_metadata, fetch_latest_state,
update_latest_global_state, ...) instead of touching database_memory._sessions
or _persist(). If the parity API lacks what you need, add it to BOTH
database.py and database_memory.py — that is the contract that keeps local
memory-mode behaviour identical to Railway's Postgres.
"""
import pathlib
import re

import pytest

BACKEND = pathlib.Path(__file__).resolve().parents[1]

# Ceiling per endpoint module, as of 2026-07-20. DOWN is progress; UP is a bug.
DEBT_CEILING = {
    "admin_router.py": 4,
    "router.py": 12,
    "admin_shared.py": 7,
    "admin_analytics.py": 1,
    "admin_teleprompter.py": 0,
}

_IMPORT_RE = re.compile(r"^\s*(from database_memory import|import database_memory)", re.M)


@pytest.mark.parametrize("fname,ceiling", sorted(DEBT_CEILING.items()))
def test_memory_store_shortcuts_do_not_grow(fname, ceiling):
    src = (BACKEND / fname).read_text(encoding="utf-8")
    count = len(_IMPORT_RE.findall(src))
    assert count <= ceiling, (
        f"{fname} now has {count} direct database_memory imports (ceiling {ceiling}). "
        "New endpoint code must use the injected `db` parity API — direct memory-store "
        "access is invisible on Postgres/Railway. See this file's docstring."
    )
    if count < ceiling:
        pytest.fail(
            f"{fname} improved to {count} direct imports (ceiling {ceiling}) — "
            f"ratchet the ceiling DOWN in DEBT_CEILING so the gain is locked in.",
        )
