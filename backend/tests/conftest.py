import os
import pytest

# Force in-memory database for all tests to prevent Postgres connection errors
# and global state pollution across tests.
#
# EXCEPTION — Postgres parity mode (2026-07-20): the memory-only default is
# precisely how a sequence of Postgres-only production bugs (immutability
# trigger, phantom _sessions writes) shipped invisibly. When PG_PARITY is set,
# tests/test_postgres_parity.py must run against REAL Postgres, so the forced
# override is skipped and the caller's USE_MEMORY_DB/DATABASE_URL win.
_PG_PARITY = os.environ.get("PG_PARITY", "").strip() in ("1", "true", "yes")
if not _PG_PARITY:
    os.environ["USE_MEMORY_DB"] = "true"

# QA-2026-07-16 #1: config.py no longer ships committed default break-glass
# passwords (unset => disabled). The suite's god_mode / project_admin login
# fixtures still use the historical values, so pin them here as TEST-ONLY
# credentials before config is imported. These are burned secrets that exist
# only inside the test process -- never set them in a real deployment.
os.environ.setdefault("MASTER_PASSWORD", "sim2026@iim")
os.environ.setdefault("PROJECT_ADMIN_PASSWORD", "simadmin2026@")

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

# ── Registry / identity-store isolation ──────────────────────────────────────
# Tests that create facilitators (bulk-delete, RBAC probes, quiz panels, …)
# call _persist_facilitators(), which previously wrote to the REAL
# db/facilitator_registry.json — every suite run leaked dozens of fixture
# accounts (BulkSoft*, C3 Gate Probe, Shockwave Probe, …) into the production
# registry, and token-version / virtual-profile writes leaked alongside.
# Repoint the persistence paths at the throwaway temp dir. The in-memory
# registry was already loaded (import time), so reads keep working; only the
# WRITES are redirected away from real state.
try:
    import admin_shared as _ash_iso
    _ash_iso._FAC_REGISTRY_PATH = str(_tmp_state / "facilitator_registry.json")
    _ash_iso._TOKEN_VERSION_PATH = str(_tmp_state / "token_versions.json")
    _ash_iso._VIRTUAL_PROFILES_PATH = str(_tmp_state / "virtual_account_profiles.json")
    _ash_iso._COHORT_STATE_PATH = str(_tmp_state / "cohort_settings.json")
except Exception:
    pass

# Pin the shared-marketplace object identity. Snapshot-restore paths
# (database_memory._apply_snapshot via _load_from_disk, used by test_res1_* and
# test_coordination_state) REASSIGN admin_shared._shared_marketplace and
# _cohort_marketplaces["default"] to a NEW object — which silently invalidates
# any module that imported the name by reference (test_new_features). Capture the
# canonical object now and restore it (with reset pools) before every test so one
# test's purchases can't leak into another.
try:
    import admin_shared as _ash_boot
    _ORIG_MARKETPLACE = _ash_boot._cohort_marketplaces["default"]
except Exception:
    _ORIG_MARKETPLACE = None


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
    # Restore the canonical shared-marketplace object + reset its pools so a prior
    # snapshot-restore test can't leave a reassigned/depleted marketplace behind.
    try:
        import admin_shared as _ash
        if _ORIG_MARKETPLACE is not None:
            _ash._cohort_marketplaces["default"] = _ORIG_MARKETPLACE
            _ash._shared_marketplace = _ORIG_MARKETPLACE
            _ORIG_MARKETPLACE["carbon_credit_pool"]["purchased"] = {}
            _ORIG_MARKETPLACE["carbon_credit_pool"]["price_history"] = [50_000]
            _ORIG_MARKETPLACE["green_talent_pool"]["hired"] = {}
            _ORIG_MARKETPLACE["green_talent_pool"]["cost_history"] = [200_000]
    except Exception:
        pass
