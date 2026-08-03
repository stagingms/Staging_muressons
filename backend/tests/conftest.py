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
# The suite must never read or write the developer's REAL runtime files under
# <repo>/db — memory_snapshot.json (game state + shared marketplace + god-mode
# and pacing settings), facilitator_registry.json, rate_bans.json,
# master_password.json.
#
# BUG-2026-07-28. The previous approach repointed module-level path constants
# AFTER importing database_memory — but database_memory calls _load_from_disk()
# at import (line ~344), so the real snapshot was already loaded by then. The
# only thing that made isolation "work" was the unlink loop that ran first:
# the suite DELETED db/memory_snapshot.json on every run. Two consequences,
# both observed:
#
#   * On a writable checkout the tests passed by destroying live state. A
#     cohort mid-simulation did not survive a test run.
#   * Where the unlink failed (read-only mount, Windows file lock, permissions)
#     it was swallowed by `except Exception: pass`, the real snapshot loaded,
#     and tests asserting platform defaults failed against whatever the
#     developer happened to have configured — e.g. test_briefing_videos
#     expecting {} and getting three real YouTube URLs.
#
# Correct isolation is environmental and must precede EVERY import: point the
# data dir at a throwaway temp dir so the path constants are computed there in
# the first place. MURESSONS_NO_LEGACY_MIGRATION stops runtime_paths.data_file()
# from helpfully copying the real files into the fresh dir, which would put us
# right back where we started. Nothing under <repo>/db is read, written or
# deleted. Do not add an unlink here.
_repo_root = backend_dir.parent
_tmp_state = pathlib.Path(tempfile.mkdtemp(prefix="mur_tests_"))
os.environ["MURESSONS_DATA_DIR"] = str(_tmp_state)
os.environ["MURESSONS_NO_LEGACY_MIGRATION"] = "1"

try:
    import rate_limit as _rl_pre
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
#
# Since the MURESSONS_DATA_DIR fix above these constants already resolve into
# the temp dir at import time, so this block is now belt-and-braces rather than
# the mechanism — and it stays for exactly that reason: it is the assertion
# that these four paths are never the real ones, independent of whether some
# future import happens to run before the env is set. Note the reads are no
# longer served by the developer's registry either (the whole point), so tests
# must create every facilitator they rely on.
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
def no_auth_state_leaks_between_tests():
    """Reset FastAPI dependency overrides after every test, and name the leaker.

    ISO-1 (2026-08-02). Running the suite in random order reveals a class of
    order-dependent failures that the default file order hides — and that CI
    hides deliberately, with `-p no:randomly` on the Postgres job:

        --randomly-seed=7   test_facilitator_bulk_delete::test_anonymous_is_refused
                            test_ceo_interview::test_ceo_interview_llm_scoring
        --randomly-seed=42  the same two, plus
                            test_shockwave_catalog_endpoint::test_catalog_route_exists_and_is_gated

    They are all authorisation tests, and the failure is the dangerous
    direction: an ANONYMOUS caller got 200 and actually deleted a facilitator —

        assert 200 == 401
        {"status":"completed","deleted":1,
         "results":[{"facilitator_id":"FAC-001","status":"deleted"}]}

    So a guard that is meant to refuse an unauthenticated request had been
    switched off by an earlier test in the same process. `app.dependency_overrides`
    is process-global and survives between test files; one `finally` that does
    not run disables that guard for every test after it.

    This fixture does two things. It CLEARS any override a test added, so the
    leak cannot propagate — and it FAILS the test that added one, so the next
    time it happens the culprit is named rather than the victim. Override
    deliberately? Pop it in a `finally`; that is all this asks.

    Note what it does NOT do: the suite may still have other order-dependent
    state (the reproduction above predates this fixture and has not been
    re-confirmed as fully closed). Run `pytest -p randomly` occasionally — and
    do not reach for `-p no:randomly` to make a red suite green. That is how
    this got here.
    """
    try:
        from main import app
    except Exception:                      # a unit test that never builds the app
        yield
        return

    before = dict(getattr(app, "dependency_overrides", {}) or {})
    try:
        yield
    finally:
        current = getattr(app, "dependency_overrides", None)
        if current is None:
            return
        leaked = {k: v for k, v in current.items() if k not in before}
        if leaked:
            current.clear()
            current.update(before)
            names = ", ".join(getattr(k, "__name__", repr(k)) for k in leaked)
            pytest.fail(
                f"this test left {len(leaked)} FastAPI dependency override(s) in place: "
                f"{names}.\n\napp.dependency_overrides is process-global. Anything left "
                "here disables that guard for every test that runs afterwards, which is "
                "how an anonymous caller came to receive 200 from a facilitator "
                "bulk-delete. Pop the override in a `finally`.",
                pytrace=False,
            )


@pytest.fixture(autouse=True)
def restore_global_rng():
    """Snapshot and restore the global RNG around every test.

    RNG-1 (2026-08-02). Eighteen test files call `random.seed(...)`; none of
    them restore it. The engine has twelve sites that draw from that same global
    stream, so whether a given tick sees a capex overrun, a micro-strike or a
    black swan depended on which test happened to run before it.

    Two consequences, both bad and both invisible: results changed under `-k`,
    `-p xdist` or `pytest-randomly`, and a green run was not evidence that the
    next run would be green. The golden traces depend on exactly the property
    this fixture provides, so it has to be autouse rather than opt-in.

    This is a workaround, not the fix. The fix is remediation #15 — route every
    draw through the seeded `event_rng` stream, at which point the global RNG
    stops being load-bearing at all.
    """
    import random as _random
    state = _random.getstate()
    try:
        yield
    finally:
        _random.setstate(state)


@pytest.fixture(autouse=True)
def no_cookie_jar_leaks_between_tests():
    """Empty every module-level TestClient's cookie jar before each test.

    AUTH-1 (2026-08-03). Twenty-six test modules build a TestClient at import
    time and share it across every test in the file. `TestClient` is an httpx
    client, and httpx keeps a COOKIE JAR: the moment any test calls
    `/facilitators/login`, the `mur_session` cookie is stored on that shared
    client and is sent automatically on every later request from it — including
    requests the test believes are anonymous.

    That is the whole of the "intermittent auth failure" that has been
    unexplained since the review. `test_facilitator_bulk_delete::
    test_anonymous_is_refused` passes in file order because it happens to run
    before any login, and fails under pytest-randomly because it does not:

        jar before login : {}
        login status     : 200
        jar AFTER login  : ['mur_session']
        'anonymous' bulk-delete -> 200 {"status":"partial", ...}
        after cookies.clear()   -> 401 {"detail":"Facilitator authentication required"}

    Note what the last two lines say. The PRODUCT is correct — a genuinely
    anonymous request is refused. The TEST was not anonymous. Seven modules
    assert some form of "unauthenticated is refused" against a shared client,
    so seven proofs of a security property were order-dependent, and the CI
    workaround (`-p no:randomly`) was hiding it rather than fixing it.

    Clearing the jar per test restores the property each of those assertions
    believes it already has: a request with no cookie is a request with no
    cookie. Tests that want authentication pass `cookies=` explicitly, which is
    unaffected — every helper in those files already does.
    """
    from fastapi.testclient import TestClient
    for name, module in list(sys.modules.items()):
        if module is None or not (name.startswith("test_") or name.startswith("tests.")):
            continue
        for value in list(getattr(module, "__dict__", {}).values()):
            if isinstance(value, TestClient):
                try:
                    value.cookies.clear()
                except Exception:      # noqa: BLE001 - hygiene, never fatal
                    pass
    yield


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
    # Solo sessions are OPT-IN in production (default OFF, 2026-08-01). ~30 test
    # modules use /solo-start as a lightweight SESSION FACTORY for testing
    # unrelated things (commit locks, investment-ratio recompute, BRSR, quiz
    # gates, …); denying it by default would break all of them for reasons that
    # have nothing to do with what they assert. So the TEST ENVIRONMENT enables
    # it here. This does NOT weaken the policy check: test_solo_mode_toggle.py
    # has its own autouse fixture that pops this key at setup (running closer to
    # the test, so after this one), verifying the true default-OFF behaviour and
    # the RBAC of the toggle explicitly.
    try:
        import admin_shared as _ash
        _ash._god_mode_settings["solo_mode_enabled"] = True
    except Exception:
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
