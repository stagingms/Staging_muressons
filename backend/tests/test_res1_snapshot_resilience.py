"""
RES-1 regression tests for the in-memory snapshot persistence.

A corrupt/unreadable primary snapshot must NEVER cause a silent empty boot:
  * _persist() keeps a rolling one-generation backup (_BACKUP_PATH).
  * _load_from_disk() on a corrupt primary logs loudly, quarantines the bad
    file (.corrupt-*), and recovers from the backup.
  * With no usable backup it starts empty but prints an unmissable notice and
    preserves the corrupt file.

Tests point the snapshot paths at a temp dir so the repo's db/ is untouched.
"""

import os

os.environ["USE_MEMORY_DB"] = "true"

import pytest

import database_memory as dm


@pytest.fixture
def tmp_snap(tmp_path, monkeypatch):
    """Redirect snapshot paths to a temp dir and restore module state after."""
    saved = (
        dm._SNAPSHOT_PATH, dm._BACKUP_PATH,
        dm._sessions, dm._global_states, dm._bu_states, dm._decision_log,
    )
    main = tmp_path / "memory_snapshot.json"
    monkeypatch.setattr(dm, "_SNAPSHOT_PATH", main)
    monkeypatch.setattr(dm, "_BACKUP_PATH", main.with_suffix(".bak"))
    yield tmp_path
    (dm._SNAPSHOT_PATH, dm._BACKUP_PATH,
     dm._sessions, dm._global_states, dm._bu_states, dm._decision_log) = saved


def _seed(tag):
    dm._sessions = {"c1": {"cohort_name": tag},
                    "sub1": {"parent_cohort_id": "c1", "player_id": "P"}}
    dm._global_states = {"sub1": [{"round_number": 1}]}
    dm._bu_states = {"sub1": {1: [{"bu_id": "pharma"}]}}
    dm._decision_log = []


def test_roundtrip_and_rolling_backup(tmp_snap):
    _seed("A")
    dm._persist()                       # first write: main only
    assert dm._SNAPSHOT_PATH.exists()
    dm._persist()                       # second write: rotates main -> .bak
    assert dm._BACKUP_PATH.exists()
    # Wipe memory and reload from the primary.
    dm._sessions, dm._global_states, dm._decision_log = {}, {}, []
    dm._bu_states = {}
    dm._load_from_disk()
    assert dm._sessions.get("c1", {}).get("cohort_name") == "A"


def test_corrupt_primary_recovers_from_backup(tmp_snap, capsys):
    _seed("GOOD")
    dm._persist()
    dm._persist()                       # .bak now holds the GOOD snapshot
    # Corrupt the primary snapshot.
    dm._SNAPSHOT_PATH.write_text("{ this is not valid json", encoding="utf-8")
    dm._sessions, dm._global_states, dm._decision_log = {}, {}, []
    dm._bu_states = {}
    dm._load_from_disk()
    # Recovered from backup...
    assert dm._sessions.get("c1", {}).get("cohort_name") == "GOOD"
    # ...corrupt file quarantined, not left in place as the primary.
    corrupt = list(tmp_snap.glob("memory_snapshot.corrupt-*.json"))
    assert len(corrupt) == 1
    out = capsys.readouterr().out
    assert "RES-1" in out and "RECOVERED" in out


def test_corrupt_primary_no_backup_starts_empty_loudly(tmp_snap, capsys):
    _seed("LONELY")
    dm._persist()                       # main only; ensure no backup exists
    if dm._BACKUP_PATH.exists():
        dm._BACKUP_PATH.unlink()
    dm._SNAPSHOT_PATH.write_text("<<corrupt>>", encoding="utf-8")
    dm._sessions = {"stale": 1}
    dm._global_states, dm._decision_log = {}, []
    dm._bu_states = {}
    dm._load_from_disk()
    # Started empty (never the stale/partial state), and loudly.
    assert dm._sessions == {}
    corrupt = list(tmp_snap.glob("memory_snapshot.corrupt-*.json"))
    assert len(corrupt) == 1
    out = capsys.readouterr().out
    assert "RES-1" in out and "EMPTY STATE" in out


def test_no_snapshot_is_normal_fresh_start(tmp_snap):
    # No files at all -> silent, clean fresh start (no error, no exception).
    dm._sessions = {"x": 1}
    dm._load_from_disk()
    # Unchanged (nothing to load); must not raise.
    assert dm._sessions == {"x": 1}
