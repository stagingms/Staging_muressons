"""
Store-access tripwire (Railway audit §1.1 remediation).

The class of bug: application code reading the MEMORY store's private dicts
(`getattr(db, '_sessions', {})`, `import database_memory`, …). Under the
Postgres store — Railway's default — those reads silently return {} / raise
ImportError, and endpoints return empty 200s with no error surface. Eight
admin endpoints, the god analytics, the agent teleprompter and four player
flows were found doing this; all are now ported to the parity db API
(`fetch_all_sessions_raw`, `fetch_round_history`, `fetch_latest_state`,
`get_session_info`, `update_session_metadata`, `fetch_all_decisions`).

This test greps the backend so the pattern cannot regrow. Legitimate
exceptions (store-mode infrastructure, or memory-only features explicitly
guarded with `_in_memory_backend_active()` + a loud 501) either live in the
allowlist below or carry a `tripwire-allow` marker on the offending line.
"""
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent

# Files that legitimately know about the memory store.
ALLOWED_FILES = {
    "database_memory.py",   # the store itself
    "database.py",          # PG store mirrors/caches into the memory module
    "main.py",              # selects the active store (sys.modules swap)
    "coordination_store.py",
    "persistence.py",
    "scale_preflight.py",
    "session_reaper.py",    # explicitly _memory_backend_active()-guarded
}

# What is and is not allowed:
#   • `database_memory._sessions` reads are a SUPPORTED mirror-cache pattern —
#     database.get_pool() hydrates all sessions into that dict under Postgres
#     (database.py:34) and create_session/get_session_info keep it warm. Reads
#     of session METADATA through the mirror therefore work in both stores.
#   • `_global_states`, `_bu_states`, `_decision_log` and `_round_states` are
#     NEVER mirrored: any reference outside the stores is a Postgres-silent
#     failure (or, for _round_states, a name that has never existed at all).
#   • `getattr(db, '_anything')` is always wrong: it degrades to {} under
#     Postgres by construction.
PATTERNS = [
    re.compile(r"getattr\(\s*db\s*,\s*['\"]_"),
    re.compile(r"\b_global_states\b"),
    re.compile(r"\b_bu_states\b"),
    re.compile(r"\b_round_states\b"),
    re.compile(r"\b_decision_log\b"),
]


def _violations():
    """Scan CODE tokens only (comments and docstrings excluded via tokenize),
    honouring `tripwire-allow` line markers and
    `tripwire-allow-block-start` / `tripwire-allow-block-end` fences."""
    import io
    import tokenize

    out = []
    for path in sorted(BACKEND.glob("*.py")):
        if path.name in ALLOWED_FILES:
            continue
        src = path.read_text(encoding="utf-8")
        lines = src.splitlines()
        allowed_lines = set()
        block = False
        for lineno, line in enumerate(lines, 1):
            if "tripwire-allow-block-start" in line:
                block = True
            if block or "tripwire-allow" in line:
                allowed_lines.add(lineno)
            if "tripwire-allow-block-end" in line:
                block = False
        try:
            tokens = tokenize.generate_tokens(io.StringIO(src).readline)
            for tok in tokens:
                if tok.type not in (tokenize.NAME, tokenize.STRING):
                    continue
                # Skip docstrings/comments: only NAME tokens and f-string-free
                # code identifiers matter; STRING tokens are skipped entirely.
                if tok.type == tokenize.STRING:
                    continue
                lineno = tok.start[0]
                if lineno in allowed_lines:
                    continue
                text = lines[lineno - 1]
                code_part = text.split("#", 1)[0]
                for pat in PATTERNS:
                    if pat.search(code_part) and pat.search(tok.string + code_part):
                        out.append(f"{path.name}:{lineno}: {text.strip()}")
                        break
        except tokenize.TokenizeError:
            # Fall back to raw line scan if tokenization fails
            for lineno, line in enumerate(lines, 1):
                if lineno in allowed_lines:
                    continue
                for pat in PATTERNS:
                    if pat.search(line.split("#", 1)[0]):
                        out.append(f"{path.name}:{lineno}: {line.strip()}")
                        break
    return sorted(set(out))


def test_no_direct_memory_store_access():
    v = _violations()
    assert not v, (
        "Direct memory-store access found — these reads silently return empty "
        "data under the Postgres store (Railway's default). Use the parity db "
        "API instead (db.fetch_all_sessions_raw / fetch_round_history / "
        "fetch_latest_state / get_session_info / update_session_metadata / "
        "fetch_all_decisions), or guard a memory-only feature with "
        "_in_memory_backend_active() + a 501 and mark the line with "
        "'tripwire-allow':\n  " + "\n  ".join(v)
    )
