import os
import pytest

# Force in-memory database for all tests to prevent Postgres connection errors
# and global state pollution across tests.
os.environ["USE_MEMORY_DB"] = "true"

# Import main immediately to force sys.modules["database"] patching
# before any other test file imports router.py or admin_router.py
import sys
import pathlib
import tempfile

# Add backend dir to sys.path so 'main' can be imported
backend_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# ── Test-state isolation ─────────────────────────────────────────────────────
# The suite was loading and writing the REAL runtime files — db/memory_snapshot.json
# (which persists the shared marketplace + god-mode/pacing state) and db/rate_bans.json
# (persisted rate-limit bans). That carried state across runs and failed the suite
# with depleted marketplace pools and stale "Too many attempts" bans. Here we:
#   1. delete any stale copies so THIS run starts clean, and
#   2. repoint the snapshot / rate-ban paths at a throwaway temp dir BEFORE main is
#      imported, so tests never load or write real runtime state again.
_repo_root = backend_dir.parent
_tmp_state = pathlib.Path(tempfile.mkdtemp(prefix="mur_tests_"))
for _stale in ("db/memory_snapshot.json", "db/memory_snapshot.bak", "db/rate_bans.json"):
    try:
        (_repo_root / _stale).unlink()
    except Exception:
        pass

try:
    import database_memory as _dm_pre
    _dm_pre._SNAPSHOT_PATH = _tmp_state / "memory_snapshot.json"
    _dm_pre._BACKUP_PATH = _tmp_state / "memory_snapshot.bak"
except Exception:
    pass

try:
    import rate_limit as _rl_pre
    _rl_pre._RATE_BAN_FILE = str(_tmp_state / "rate_bans.json")
    _rl_pre._persistent_bans.clear()
    _rl_pre._rate_buckets.clear()
except Exception:
    pass

import main

@pytest.fixture(autouse=True)
def clear_memory_db():
    """Clear transient global state before every test so nothing cascades."""
    try:
        import database_memory as _db
        _db._sessions.clear()
        _db._global_states.clear()
        _db._bu_states.clear()
        _db._decision_log.clear()
    except ImportError:
        pass
    # Rate-limit buckets/bans are per-process and otherwise accumulate across
    # tests, causing the "Too many attempts" cascade. Reset them per test so each
    # test starts with a clean limiter (a test that wants to trigger the limit
    # still does its own repeated calls).
    try:
        import rate_limit as _rl
        _rl._rate_buckets.clear()
        _rl._persistent_bans.clear()
    except Exception:
        pass
