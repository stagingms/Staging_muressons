# Pre-deploy verification — run this before pushing to Railway

Three layers, cheapest first. Stop and fix at the first one that fails; a
later layer passing does not excuse an earlier one failing.

---

## Layer 1 — Automated tests (2 minutes, no server needed)

```bat
cd backend
python -m pytest tests\ -q
```

Expect **1448 passed**. These run in-process and cover the engine, auth,
provisioning, and deployment hygiene.

```bat
cd frontend
npm test
```

---

## Layer 2 — Smoke test against a real running server (5 minutes)

This is the one that matters most, because it drives real HTTP the way a
browser does — uvicorn actually booting, `.env` actually loading, cookies,
CORS, and which database is really in use. None of that is visible to Layer 1.

**Terminal 1** — start the stack:

```bat
start.bat
```

Wait for the backend window to print `Application startup complete`.

**Terminal 2** — run the smoke test:

```bat
pip install requests openpyxl
python scripts\smoke_local.py
```

Expect `All checks passed — ready to deploy.` It creates a `SMOKE-*` cohort,
exercises login, the round-1 seed, both upload templates, all-or-nothing
rejection, bulk creation, player login, password reveal, hash leakage and the
roster cap — then deletes the cohort.

If it fails, the output names the fix. The two most common:

| Symptom | Cause |
|---|---|
| `god_mode login failed (403)` | A rotated `master_password.json` overrides `.env`. Delete `db\master_password.json` and `backend\db\master_password.json`. |
| `backend is not reachable` | Backend isn't running, or it's on a different port. |

### Also run it against PostgreSQL — NON-NEGOTIABLE before a deploy push

**This is the single biggest local/production divergence, and it has shipped
real outages.** `start.bat` sets `USE_MEMORY_DB=true`; Railway runs PostgreSQL.
The round-state immutability trigger only exists on Postgres — it 500'd
CEO-Interview saves and Double-Materiality submissions in production while all
1,485 memory-mode tests stayed green. The smoke test WARNs when it detects the
memory store; treat that warning as a failure for deploy purposes.

With Docker Desktop running:

```bat
docker compose -f docker-compose.dev.yml up -d

cd backend
set USE_MEMORY_DB=false
python -m uvicorn main:app --port 8000
```

Then in Terminal 2:

```bat
python scripts\smoke_local.py          REM must pass with NO memory-store warning
cd backend
set PG_PARITY=1
python -m pytest tests/test_postgres_parity.py -q
```

The parity suite replays the exact flows that broke in production (CEO config,
materiality submit, cohort settings, player credentials) against real Postgres.
CI runs the same suite on every push (`backend-postgres` job); with Railway's
**Wait for CI** enabled, a deploy cannot start until it is green.

Restart the backend once more afterwards and confirm your cohorts and
facilitators are still there — that proves durability, which is the entire
reason for using Postgres in production.

---

## Layer 3 — Manual UI pass (15 minutes)

A script cannot see rendering. Open http://localhost:3000/admin and check:

**Login and tour**
- [ ] Sign in as `god_mode` / your `MASTER_PASSWORD`
- [ ] Facilitator tour: each card's highlighted region is **clearly visible**,
      not dimmed (the July-2026 spotlight fix)
- [ ] Forced password modal, if shown, appears *before* the tour, not on top of it

**Player Registry** (Live Classroom → Player Registry)
- [ ] Create a cohort; badge reads `0/20 Inducted`
- [ ] **+ Generate Player ID** → the password is visible immediately,
      **not** `— (reset to reveal)`
- [ ] **📥 Bulk Upload** → Download template → fill 3 rows → Preview → Create
- [ ] Roster shows Name, Player ID, **Programme**, Assigned BU
- [ ] Log in as one uploaded player in a private window with the shown password

**Master provisioning** (Facilitator Manager → Bulk Upload)
- [ ] **🏛️ Open Master Provisioning Upload** → Download template
- [ ] Upload it unmodified → Preview reports 1 facilitator, 2 cohorts, 3 players
- [ ] Create → the new facilitator, cohorts and players all appear

**A full round**
- [ ] Play round 1 as a player through to commit
- [ ] Results render; the leaderboard updates
- [ ] Advance a round from the facilitator dashboard

---

## Layer 4 — Deployment config (before you push)

- [ ] `del db\.write_probe` if present (stray file from an earlier preflight)
- [ ] Railway Variables match `backend\.env.railway`
- [ ] **A Railway Volume is mounted at `/data`** — without it, every redeploy
      wipes the facilitator registry. This is the most common Railway mistake.
- [ ] Postgres plugin added and referenced by the service
- [ ] After first deploy, check the logs for
      `[preflight] Deployment configuration looks correct.`
      Any warning block there names exactly what to fix.

---

## What "ready" means

| Layer | Signal |
|---|---|
| 1 | 1448 backend tests pass |
| 2 | `All checks passed`, on **both** memory and Postgres |
| 3 | Every box above ticked |
| 4 | Clean preflight in the Railway logs |
