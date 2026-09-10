"""RES-1 regression found on the 2026-09-10 drill server's boot log:

    [persistence] Load error: name '_load_commit_results_journal' is not defined

database_memory restores its snapshot AT IMPORT (the module-level
_load_from_disk() call sits below the loader). The F06b journal helpers
were defined further down the file, so _apply_snapshot raised NameError
on every boot that found a snapshot — and RES-1, reading that as a corrupt
file, QUARANTINED the live snapshot and started empty. No test saw it:
the suite points the data dir at an empty temp dir (nothing to restore)
and the round-trip test calls _load_from_disk() after import.

This test does what a restart does: writes a real snapshot, then imports
the module in a fresh interpreter against that directory.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile

_BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent


def test_a_fresh_interpreter_restores_the_snapshot_it_finds():
    d = pathlib.Path(tempfile.mkdtemp(prefix="mur_boot_"))
    env = {**os.environ, "USE_MEMORY_DB": "true", "MURESSONS_DATA_DIR": str(d),
           "MURESSONS_NO_LEGACY_MIGRATION": "1", "PYTHONDONTWRITEBYTECODE": "1",
           "JWT_SECRET": os.environ.get("JWT_SECRET", "testsecret0123456789abcdefabcdef")}
    writer = r"""
import asyncio, database_memory as dm
async def go():
    s = await dm.create_session(cohort_name="boot-probe", facilitator_id="god_mode")
    await dm.save_commit_result(s["session_id"], 1, {"round_committed": 1, "new_round_number": 2, "events": {"k": 1},
                                                    "global_state": {}, "business_units": []})
    return s["session_id"]
sid = asyncio.run(go())
dm._write_snapshot_now()
print(sid)
"""
    r = subprocess.run([sys.executable, "-c", writer], cwd=_BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-800:]
    sid = r.stdout.strip().splitlines()[-1]
    assert (d / "memory_snapshot.json").exists()

    reader = r"""
import asyncio, database_memory as dm
print("SESSIONS", len(dm._sessions))
print("RESULT", asyncio.run(dm.fetch_commit_result(%r, 1)) is not None)
""" % sid
    r2 = subprocess.run([sys.executable, "-c", reader], cwd=_BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120)
    assert r2.returncode == 0, r2.stderr[-800:]
    out = r2.stdout + r2.stderr
    assert "SESSIONS 1" in out, out[-600:]
    assert "RESULT True" in out, out[-600:]
    assert "PRIMARY SNAPSHOT UNREADABLE" not in out and "STARTING WITH EMPTY STATE" not in out, out[-900:]
    assert not list(d.glob("*.corrupt-*")), "the live snapshot was quarantined at boot"
