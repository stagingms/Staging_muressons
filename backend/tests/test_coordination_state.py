"""Audit Fix #5/#6 — shared coordination state + db-routed session mutations.

Covers the memory-mode behaviour (the path the suite runs in):
  #5  pacing policy + God-Mode settings survive a snapshot round-trip
      (restart-durability) and the JSON-safe view strips per-process asyncio
      timer handles so it can be shipped to another worker / serialised.
  #6  session field mutations routed through db.update_session_metadata are
      persisted (the solo-start durability bug).

The Postgres cross-worker path is not exercised here (needs a live PG + >1
worker — audit item #8); coordination_store is a no-op in memory mode.
"""

import asyncio

import admin_shared as a
import coordination_store as cs
import database_memory as db


def test_pacing_snapshot_strips_asyncio_handles():
    a._round_pacing["COORD_S1"] = {
        "mode": "timed", "unlocked_round": 4, "set_by": "fac-1",
        "_timer_tasks": [object()], "_timer_task": object(),
    }
    snap = a.pacing_policy_snapshot("COORD_S1")
    assert "_timer_tasks" not in snap and "_timer_task" not in snap
    assert snap["mode"] == "timed" and snap["unlocked_round"] == 4
    assert snap["set_by"] == "fac-1"


def test_restore_pacing_keeps_local_timer_fields():
    a._round_pacing.pop("COORD_S2", None)
    a.restore_pacing_policy("COORD_S2", {"mode": "timed", "unlocked_round": 7})
    p = a._round_pacing["COORD_S2"]
    assert p["unlocked_round"] == 7
    # _get_pacing re-seeds the per-process timer containers on restore.
    assert "_timer_tasks" in p and "_timer_task" in p


def test_godmode_settings_round_trip():
    a._god_mode_settings["system_frozen"] = True
    a._god_mode_settings["freeze_message"] = "maintenance"
    saved = a.godmode_settings_snapshot()
    a._god_mode_settings["system_frozen"] = False
    a._god_mode_settings["freeze_message"] = ""
    a.restore_godmode_settings(saved)
    assert a._god_mode_settings["system_frozen"] is True
    assert a._god_mode_settings["freeze_message"] == "maintenance"


def test_memory_backend_is_not_shared_by_default():
    # Without an explicit Postgres configure(), coordination is a local no-op and
    # durability rides the snapshot — so mark_* helpers must take the memory path.
    assert cs.is_shared() is False
    assert a._in_memory_backend_active() is True


def test_snapshot_persists_pacing_and_godmode(tmp_path, monkeypatch):
    """#5 restart-durability: a snapshot written now must carry pacing + god-mode
    settings, and applying it into cleared dicts must restore them."""
    a._round_pacing["COORD_S3"] = {
        "mode": "manual", "unlocked_round": 2, "set_by": "fac-9",
        "_timer_tasks": [], "_timer_task": None,
    }
    a._god_mode_settings["system_frozen"] = True

    snap_path = tmp_path / "snap.json"
    monkeypatch.setattr(db, "_SNAPSHOT_PATH", snap_path)
    monkeypatch.setattr(db, "_BACKUP_PATH", snap_path.with_suffix(".bak"))
    db._persist()
    assert snap_path.exists()

    saved = db._read_snapshot(snap_path)
    assert saved["round_pacing"]["COORD_S3"]["unlocked_round"] == 2
    assert "_timer_task" not in saved["round_pacing"]["COORD_S3"]
    assert saved["god_mode_settings"]["system_frozen"] is True

    # Simulate a restart: wipe the live dicts, then apply the snapshot.
    a._round_pacing.pop("COORD_S3", None)
    a._god_mode_settings["system_frozen"] = False
    db._apply_snapshot(saved)
    assert a._round_pacing["COORD_S3"]["unlocked_round"] == 2
    assert a._god_mode_settings["system_frozen"] is True


def test_update_session_metadata_routes_and_persists():
    """#6: session field writes go through the db interface and stick."""
    async def _run():
        res = await db.create_session(cohort_name="Coord Test Cohort", facilitator_id=None)
        sid = str(res["session_id"])
        ok = await db.update_session_metadata(sid, {"is_solo": True, "pacing_mode": "free_play"})
        assert ok is True
        info = await db.get_session_info(sid)
        assert info.get("is_solo") is True
        assert info.get("pacing_mode") == "free_play"
    asyncio.run(_run())
