#!/usr/bin/env python3
"""smoke_local.py — pre-deploy smoke test against a RUNNING local server.

    python scripts/smoke_local.py

Why a separate script when there are 1448 pytest tests: those run in-process
with a synthetic TestClient. This drives the real HTTP server the way a
browser does, so it also exercises the things the test suite cannot see —
uvicorn actually booting, the .env file actually loading, CORS, cookie flags,
and whether the database you configured is the one really in use.

Exit code 0 = safe to deploy. Non-zero = something to fix first.

Nothing here is destructive to existing data: every cohort it creates is
named with a SMOKE- prefix and removed at the end. If the run dies partway,
delete any leftover SMOKE-* cohorts from the Player Registry.
"""
from __future__ import annotations

import argparse
import io
import sys
import time

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests")

try:
    from openpyxl import Workbook
except ImportError:
    sys.exit("Missing dependency: pip install openpyxl")


BASE = "http://127.0.0.1:8000"
PASSES, FAILS, WARNS = [], [], []
SUFFIX = str(int(time.time()))[-6:]


def ok(msg):
    PASSES.append(msg)
    print(f"  \033[92mPASS\033[0m  {msg}")


def bad(msg, detail=""):
    FAILS.append(msg)
    print(f"  \033[91mFAIL\033[0m  {msg}")
    if detail:
        print(f"        {str(detail)[:300]}")


def warn(msg):
    WARNS.append(msg)
    print(f"  \033[93mWARN\033[0m  {msg}")


def section(title):
    print(f"\n\033[1m{title}\033[0m")


def roster_xlsx(rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Players"
    ws.append(["name", "email", "programme", "assigned_bu", "region_id"])
    for r in rows:
        ws.append(list(r))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE, help=f"backend URL (default {BASE})")
    ap.add_argument("--god-password", default=None,
                    help="MASTER_PASSWORD; read from backend/.env if omitted")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    god_pw = args.god_password
    if not god_pw:
        try:
            import pathlib
            envf = pathlib.Path(__file__).resolve().parents[1] / "backend" / ".env"
            for line in envf.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("MASTER_PASSWORD="):
                    god_pw = line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            pass
    if not god_pw:
        sys.exit("Could not read MASTER_PASSWORD from backend/.env — pass --god-password")

    s = requests.Session()
    print(f"\n\033[1mMuressons local smoke test\033[0m  →  {base}")
    print(f"Using MASTER_PASSWORD from backend/.env ({god_pw[:3]}…)")

    # ── 1. Server is up ─────────────────────────────────────────────────────
    section("1. Server")
    try:
        r = s.get(f"{base}/health", timeout=10)
        ok(f"backend responds on {base} ({r.status_code})")
    except Exception as exc:
        bad("backend is not reachable", exc)
        print("\n  Start it first:  cd backend && python -m uvicorn main:app --port 8000")
        return 1

    # Which store is live? This is the single biggest local/production
    # divergence — a smoke test that passes on the memory store proves nothing
    # about the Postgres path Railway will use.
    try:
        body = r.json()
        mode = str(body.get("database", body.get("db", ""))).lower()
        if "memory" in mode:
            warn("running on the IN-MEMORY store. Railway will use PostgreSQL. "
                 "Re-run with USE_MEMORY_DB=false against a local Postgres to "
                 "exercise the same code path (see the runbook).")
        elif mode:
            ok(f"database mode: {mode}")
    except Exception:
        pass

    # ── 2. Authentication ───────────────────────────────────────────────────
    section("2. Authentication")
    r = s.post(f"{base}/api/admin/facilitators/login",
               json={"facilitator_id": "god_mode", "password": god_pw}, timeout=10)
    if r.status_code == 200 and r.json().get("role") == "god_mode":
        ok("god_mode logs in and resolves to role 'god_mode'")
    else:
        bad(f"god_mode login failed ({r.status_code})", r.text)
        if r.status_code == 403:
            print("        A rotated master_password.json overrides your .env value.")
            print("        Delete db\\master_password.json and backend\\db\\master_password.json.")
        return 1

    r = s.post(f"{base}/api/admin/facilitators/login",
               json={"facilitator_id": "god_mode", "password": "definitely-wrong-xyz"}, timeout=10)
    if r.status_code in (401, 403):
        ok("a wrong password is rejected")
    elif r.status_code == 429:
        warn("rate limiter engaged before the negative test could run (not a defect)")
    else:
        bad(f"wrong password returned {r.status_code} — expected 403")
    s.post(f"{base}/api/admin/facilitators/login",
           json={"facilitator_id": "god_mode", "password": god_pw}, timeout=10)

    # ── 3. Cohort + round engine ────────────────────────────────────────────
    section("3. Cohort and round engine")
    sid = None
    r = s.post(f"{base}/api/simulations/start",
               json={"cohort_name": f"SMOKE-{SUFFIX}", "facilitator_id": "god_mode"}, timeout=30)
    if r.status_code in (200, 201) and r.json().get("session_id"):
        payload = r.json()
        sid = str(payload["session_id"])
        ok(f"cohort created ({sid[:8]}…)")
        # /start returns the seeded round-1 state, so the engine has run. There
        # is no separate GET state route — the player dashboard reads its state
        # from this same response shape.
        gs = payload.get("global_state") or {}
        # StartSessionResponse names the list `business_units` (models.py:222).
        bus = payload.get("business_units") or []
        if gs.get("corporate_treasury") is not None and bus:
            ok(f"round-1 seeded: treasury={gs['corporate_treasury']:,}, {len(bus)} business units")
        else:
            bad("cohort created but round-1 state is empty — the seed did not load", payload)
    else:
        bad(f"cohort creation failed ({r.status_code})", r.text)
        return 1

    r = s.get(f"{base}/api/simulations/{sid}/session-info", timeout=20)
    if r.status_code == 200:
        info = r.json()
        ok(f"session metadata readable (paradigm={info.get('decision_paradigm')}, "
           f"currency={info.get('currency_symbol')})")
    else:
        bad(f"could not read session metadata ({r.status_code})", r.text)

    # ── 4. Player provisioning (the July-2026 work) ─────────────────────────
    section("4. Player provisioning")
    r = s.get(f"{base}/api/admin/players/bulk-template", timeout=20)
    if r.status_code == 200 and r.content[:2] == b"PK":
        ok("player roster template downloads as a real .xlsx")
    else:
        bad(f"roster template failed ({r.status_code})")

    r = s.get(f"{base}/api/admin/provisioning/master-template", timeout=20)
    if r.status_code == 200 and r.content[:2] == b"PK":
        ok("master provisioning template downloads as a real .xlsx")
    else:
        bad(f"master template failed ({r.status_code})")

    files = {"file": ("roster.xlsx", io.BytesIO(roster_xlsx([
        ["Smoke One", "s1@example.edu", "MBA 2026", "", ""],
        ["Smoke Two", "s2@example.edu", "", "", ""],
    ])), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = s.post(f"{base}/api/admin/{sid}/players/bulk-preview", files=files, timeout=30)
    if r.status_code == 200 and r.json().get("ok"):
        ok(f"bulk PREVIEW validates the file (remaining capacity: {r.json().get('remaining')})")
    else:
        bad(f"bulk preview failed ({r.status_code})", r.text)

    files = {"file": ("bad.xlsx", io.BytesIO(roster_xlsx([
        ["Good Row", "g@example.edu", "", "", ""],
        ["Bad Row", "not-an-email", "", "", ""],
    ])), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = s.post(f"{base}/api/admin/{sid}/players/bulk-upload", files=files, timeout=30)
    if r.status_code == 400:
        ok("a file with one bad row is rejected whole (all-or-nothing)")
    else:
        bad(f"bad file returned {r.status_code} — expected 400")

    files = {"file": ("roster.xlsx", io.BytesIO(roster_xlsx([
        ["Smoke One", "s1@example.edu", "MBA 2026", "", ""],
        ["Smoke Two", "s2@example.edu", "", "", ""],
    ])), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = s.post(f"{base}/api/admin/{sid}/players/bulk-upload", files=files, timeout=30)
    created = []
    if r.status_code == 200:
        created = r.json().get("created", [])
        ok(f"bulk upload created {len(created)} players with temp passwords")
        if created and created[0].get("programme") == "MBA 2026":
            ok("demographics (programme) round-trip correctly")
        else:
            bad("programme did not survive the upload")
    else:
        bad(f"bulk upload failed ({r.status_code})", r.text)

    # ── 5. Credentials actually work ────────────────────────────────────────
    section("5. Credentials")
    if created:
        cred = created[0]
        r = s.post(f"{base}/api/simulations/player-login",
                   json={"player_id": cred["player_id"], "password": cred["temp_password"]},
                   timeout=20)
        if r.status_code == 200:
            ok(f"uploaded player {cred['player_id']} can log in with their temp password")
            if r.json().get("must_change_password") is True:
                ok("first login forces a password change")
        else:
            bad(f"uploaded player cannot log in ({r.status_code})", r.text)

        lb = s.get(f"{base}/api/admin/leaderboard", timeout=30)
        row = next((x for x in lb.json().get("leaderboard", []) if x["session_id"] == sid), None)
        if row is None:
            bad("cohort missing from the leaderboard payload")
        else:
            entry = next((p for p in row.get("registered_players", [])
                          if p["player_id"] == cred["player_id"]), None)
            if entry and entry.get("temp_password") == cred["temp_password"]:
                ok("temp password is REVEALABLE in the roster (no reset needed)")
            else:
                bad("temp password is not visible in the roster — the reveal fix is not live")
            if entry and "password" not in entry and "plaintext_password" not in entry:
                ok("no bcrypt hash is exposed to the browser")
            else:
                bad("roster payload leaks a password hash")
            if row.get("max_players") == 20:
                ok("cohort roster cap is 20")
            else:
                warn(f"cohort cap is {row.get('max_players')} (expected 20)")

    # ── 6. Cleanup ──────────────────────────────────────────────────────────
    section("6. Cleanup")
    if sid:
        r = s.delete(f"{base}/api/admin/sessions/{sid}", timeout=30)
        if r.status_code in (200, 204):
            ok("smoke cohort deleted")
        else:
            warn(f"could not delete SMOKE-{SUFFIX} ({r.status_code}) — remove it manually")

    # ── Verdict ─────────────────────────────────────────────────────────────
    print("\n" + "─" * 66)
    print(f"  {len(PASSES)} passed, {len(FAILS)} failed, {len(WARNS)} warnings")
    if FAILS:
        print("\n  \033[91mNOT ready to deploy.\033[0m Fix:")
        for f in FAILS:
            print(f"    • {f}")
        return 1
    if WARNS:
        print("\n  \033[93mReady, with caveats:\033[0m")
        for w in WARNS:
            print(f"    • {w}")
    else:
        print("\n  \033[92mAll checks passed — ready to deploy.\033[0m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
