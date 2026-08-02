"""The test suite must not read, write, or DELETE the developer's live state.

BUG-2026-07-28. conftest repointed database_memory._SNAPSHOT_PATH *after*
importing database_memory — but that module calls _load_from_disk() at import
time, so the real db/memory_snapshot.json had already been loaded. The only
thing keeping the suite "isolated" was the line that ran first:

    for _stale in ("db/memory_snapshot.json", ...):
        try: (_repo_root / _stale).unlink()
        except Exception: pass

i.e. running pytest DELETED the developer's live simulation state. Verified by
seeding a snapshot holding a cohort and running one test file: the tests
passed and the cohort was gone.

Where the unlink could not succeed — a read-only mount, a Windows file lock,
restrictive permissions — the bare `except Exception: pass` swallowed it, the
real snapshot loaded, and tests asserting platform defaults failed against
whatever that developer happened to have configured. test_briefing_videos
expected {} and got three real YouTube URLs from a live install. Same root
cause, opposite symptom, which is why it read as flaky rather than dangerous.

Isolation now happens through the environment BEFORE any import
(MURESSONS_DATA_DIR + MURESSONS_NO_LEGACY_MIGRATION in conftest), so the path
constants are computed against a temp dir in the first place and nothing is
ever copied in or removed.
"""
import os
import pathlib
import re

BACKEND = pathlib.Path(__file__).resolve().parents[1]
REPO_DB = BACKEND.parent / "db"
CONFTEST = (BACKEND / "tests" / "conftest.py").read_text(encoding="utf-8")


def test_runtime_state_is_not_resolved_into_the_repo_db_dir():
    """The single assertion that would have caught this: where does the
    snapshot actually live while the suite runs?"""
    import database_memory as dm
    snapshot = pathlib.Path(dm._SNAPSHOT_PATH).resolve()
    assert REPO_DB.resolve() not in snapshot.parents, (
        f"the suite resolved its snapshot to {snapshot}, inside the repo's "
        "live db/ — tests are running against real state"
    )


def test_the_data_dir_env_is_set_and_migration_is_disabled():
    """Both halves are load-bearing. MURESSONS_DATA_DIR alone is not
    isolation: data_file() would migrate the real files into the temp dir."""
    assert os.environ.get("MURESSONS_DATA_DIR"), "conftest must set a temp data dir"
    assert os.environ.get("MURESSONS_NO_LEGACY_MIGRATION", "").lower() in ("1", "true", "yes")

    import runtime_paths
    assert runtime_paths.data_dir().resolve() != REPO_DB.resolve()


def test_identity_stores_resolve_outside_the_repo():
    """Facilitator accounts and the master-password override are the two that
    hurt most: leaked fixture accounts, and a stale master_password.json
    silently overriding the env password."""
    import admin_shared
    for attr in ("_FAC_REGISTRY_PATH", "_TOKEN_VERSION_PATH", "_VIRTUAL_PROFILES_PATH"):
        p = pathlib.Path(getattr(admin_shared, attr)).resolve()
        assert REPO_DB.resolve() not in p.parents, f"{attr} points into the live db/: {p}"


def test_conftest_never_deletes_repo_state():
    """The regression itself. No unlink/remove/rmtree targeting the repo."""
    for pattern in (r"\.unlink\(", r"os\.remove\(", r"shutil\.rmtree\(", r"\.write_text\("):
        for m in re.finditer(pattern, CONFTEST):
            line = CONFTEST[CONFTEST.rfind("\n", 0, m.start()) + 1:
                            CONFTEST.find("\n", m.end())]
            assert "_repo_root" not in line and "_REPO_DB" not in line, (
                f"conftest mutates repo state: {line.strip()!r}. Isolate via "
                "MURESSONS_DATA_DIR instead — never by deleting real files."
            )


def test_conftest_sets_the_data_dir_before_importing_the_app():
    """Ordering is the whole bug: database_memory calls _load_from_disk() at
    import, so an env set after `import main` is already too late."""
    env_at = CONFTEST.find('os.environ["MURESSONS_DATA_DIR"]')
    main_at = CONFTEST.find("\nimport main")
    assert env_at > -1, "conftest must set MURESSONS_DATA_DIR"
    assert main_at > -1
    assert env_at < main_at, (
        "MURESSONS_DATA_DIR is set AFTER `import main` — the snapshot path is "
        "bound at import, so the real state is loaded before the override lands"
    )


def test_database_memory_still_loads_at_import():
    """Pins the constraint that makes ordering matter. If this ever becomes
    lazy the ordering rule can relax — until then it must not silently drift."""
    src = (BACKEND / "database_memory.py").read_text(encoding="utf-8")
    assert re.search(r"^_load_from_disk\(\)", src, re.M), (
        "database_memory no longer loads at import — re-check whether "
        "conftest's ordering requirement still holds"
    )
