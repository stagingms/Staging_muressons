"""The two storage backends must present ONE surface. Class-level tripwire.

FIVE production incidents came from the same shape — code written against the
memory backend, silently wrong or crashing under Postgres:

  1. get_effective_settings / cohort-id resolution (negotiation rooms 403)
  2. God-Mode counters read db._sessions → always 0 cohorts on Postgres
  3. player-login's registry-miss fallback read db._sessions → 500 for every
     player missing from the in-process registry ("unable to login")
  4. create_session seeded industry/region flags only in memory → every
     uploaded vertical/regional config invisible in production play
  5. resolve_join_code / get_decision_log / _persist existed only in memory →
     short-code join 500'd; decision views 500'd; a scrubbed plaintext temp
     password RESURFACED after restart because the scrub never persisted

Unit tests never catch these: in memory mode `sys.modules["database"]` is
aliased to database_memory, so `import database as db` hands every test the
backend that has everything. These checks therefore parse SOURCE, not runtime.
"""
import ast
import pathlib
import re

import pytest

_BACKEND = pathlib.Path(__file__).resolve().parents[1]


def _module_attrs(fname: str) -> set[str]:
    """Top-level names a module exposes: defs, assigns, and imports."""
    tree = ast.parse((_BACKEND / fname).read_text(encoding="utf-8"))
    names: set[str] = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            names.add(n.target.id)
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                names.add(a.asname or a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                names.add((a.asname or a.name).split(".")[0])
    return names


def _public_fns(fname: str) -> dict[str, list[str]]:
    tree = ast.parse((_BACKEND / fname).read_text(encoding="utf-8"))
    return {n.name: [a.arg for a in n.args.args]
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not n.name.startswith("_")}


# Deliberately one-sided helpers. ADDING to this list requires a reason: every
# name here is invisible to the other backend and will crash `db.<name>`.
_MEMORY_ONLY: frozenset = frozenset({
    # (currently none — keep it that way)
})
_POSTGRES_ONLY: frozenset = frozenset({
    "get_pool_release",   # pool diagnostics; never called through the alias
})


def test_every_public_function_exists_in_both_backends():
    mem = _public_fns("database_memory.py")
    pg = _public_fns("database.py")
    only_mem = set(mem) - set(pg) - _MEMORY_ONLY
    only_pg = set(pg) - set(mem) - _POSTGRES_ONLY
    assert not only_mem, (
        f"memory-only public functions {sorted(only_mem)} — any `db.X` caller "
        "500s under Postgres (incident class #3/#5)")
    assert not only_pg, (
        f"postgres-only public functions {sorted(only_pg)} — any `db.X` caller "
        "crashes in memory mode")


def test_shared_functions_have_identical_signatures():
    mem = _public_fns("database_memory.py")
    pg = _public_fns("database.py")
    diffs = {k: (mem[k], pg[k]) for k in set(mem) & set(pg) if mem[k] != pg[k]}
    assert not diffs, (
        f"signature drift {diffs} — a keyword caller works in one mode and "
        "TypeErrors in the other")


def test_every_db_attribute_used_by_the_app_exists_in_both_backends():
    """The generic form of the db._sessions / _persist / resolve_join_code
    incidents: every `db.X` / `_db.X` token in the app layer must resolve in
    BOTH modules, because which module answers depends on USE_MEMORY_DB."""
    mem_attrs = _module_attrs("database_memory.py")
    pg_attrs = _module_attrs("database.py")
    used: set[str] = set()
    for fname in ("router.py", "admin_router.py", "admin_analytics.py", "main.py"):
        src = (_BACKEND / fname).read_text(encoding="utf-8")
        # CODE only — a comment narrating a dead pattern must not re-flag it.
        code = "\n".join(line.split("#", 1)[0] for line in src.splitlines())
        # `import database as db` / `import database as _db` callers
        used |= set(re.findall(r"\b_?db\.([A-Za-z_][A-Za-z0-9_]*)", code))
    missing_pg = sorted(a for a in used if a in mem_attrs and a not in pg_attrs)
    missing_mem = sorted(a for a in used if a in pg_attrs and a not in mem_attrs)
    assert not missing_pg, (
        f"app code uses db.{missing_pg} which only the MEMORY backend has — "
        "this is a production 500 (or a silently-swallowed no-op) on Postgres")
    assert not missing_mem, (
        f"app code uses db.{missing_mem} which only the POSTGRES backend has")


def _seeded_flag_keys(fname: str) -> set[str]:
    """String keys literally seeded into the round-1 flags dict inside
    create_session. Coarse by design: it need only agree between the twins."""
    src = (_BACKEND / fname).read_text(encoding="utf-8")
    i = src.index("async def create_session")
    j = src.index("async def", i + 10)
    body = src[i:j]
    m = re.search(r"flags\s*=\s*\{(.*?)\n\s*\}", body, re.S) \
        or re.search(r'"active_event_flags":\s*\{(.*?)\n\s*\}', body, re.S)
    assert m, f"could not locate the flags seed block in {fname}"
    return set(re.findall(r'"([a-z0-9_]+)":', m.group(1)))


# Keys one backend seeds structurally elsewhere (verified manually; each entry
# must name where the other backend provides the equivalent).
_SEED_EQUIVALENTS: frozenset = frozenset({
    # memory seeds these in the flags block; postgres carries them as
    # explicit columns / later writes on the same round row:
    "loan_interest_rate",   # both seed it (kept for symmetric diff below)
    "ending_pathway",       # router.py:1111 writes it post-create in both modes
})


def test_create_session_seeds_the_same_flag_keys():
    """Incident #4 generalised: a key seeded by one twin and not the other is
    invisible scope in one storage mode."""
    mem = _seeded_flag_keys("database_memory.py") - _SEED_EQUIVALENTS
    pg = _seeded_flag_keys("database.py") - _SEED_EQUIVALENTS
    only_mem = mem - pg
    only_pg = pg - mem
    # postgres seeds bookkeeping keys at the flags level that memory carries
    # as explicit row fields — that direction is safe (memory's fetch returns
    # them either way). The DANGEROUS direction is memory-only seeds.
    assert not only_mem, (
        f"flag keys seeded only by the MEMORY backend: {sorted(only_mem)} — "
        "under Postgres these are absent from round state and every resolver "
        "reading them silently falls back (incident #4)")
    assert only_pg <= {
        "bonus_score", "historical_ebitda", "tco2e_emissions",
        "vrio_capabilities", "green_transition_fund", "tipping_point_active",
        "pending_capex_projects", "inflation_index", "competitor_ebitda",
    }, f"unexpected postgres-only seeds {sorted(only_pg)} — verify memory parity"
