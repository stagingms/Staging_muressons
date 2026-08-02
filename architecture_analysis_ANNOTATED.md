# Muressons Architecture Review — Annotated Assessment

**Reviewer:** Claude (Cowork) · **Date:** 2026-07-21
**Method:** Every claim below was checked against the code currently on disk — `Dockerfile`, `docker-start.sh`, `railway.json`, `frontend/next.config.mjs`, `backend/main.py`, `backend/database.py`, `db/init.sql`, `docker-compose*.yml`, `DEPLOYMENT_CHECKLIST.md`. File:line evidence is cited inline.

---

## TL;DR

The original review is well-written and its *recommendations* are mostly sound, but it appears to have been written against an **earlier commit**. Most of the "Critical" section describes problems that are **already fixed** in the current code. Handing it over as-is would send someone to re-solve solved problems.

**Net verdict per claim:**

| # | Claim | Verdict |
|---|---|---|
| 1 | Dead backend reports "healthy" via frontend health-check | ❌ Mostly wrong — already mitigated |
| 2 | No database — all data lost on restart | 🟠 Overstated, but contains the ONE genuinely open action |
| 3 | Secrets baked into Dockerfile `ENV` | ❌ False — already removed |
| 4 | Giant monolithic files | ✅ Valid (line numbers slightly inflated) |
| 5 | Dual DB backends drift | ✅ Valid |
| 6 | No active CI | 🟠 Conclusion plausible, stated reason is wrong |
| 7 | CORS not configured → login fails | ❌ Largely incorrect for this architecture |
| — | "491 automated tests" | 🟠 Outdated — actual ≈ 1,083 |

**The single thing actually worth doing:** provision PostgreSQL on Railway, **apply `db/init.sql` to it once**, set `DATABASE_URL`, and remove the `ALLOW_MEMORY_DB_IN_PROD` override so the app runs on durable storage. Steps are in the last section.

---

## 🔴 Critical Problems (original)

### 1. Single-Container Monolith

> **Original claim:** If the frontend crashes the container is left half-alive; Railway's health-check hits `/api/health` (frontend), so a dead backend reports "healthy" while the API is down.

**🔍 Evaluation — ❌ Mostly wrong (already mitigated).**

- `docker-start.sh` wraps **both** the backend and the frontend in restart loops — the frontend loop is explicitly labelled *"Review C2 — frontend SPOF."* A crash of either process is restarted in ~3s.
- The health-check does **not** bypass the backend. `railway.json` sets `healthcheckPath: /api/health`; `frontend/next.config.mjs` rewrites `/api/:path*` → `${BACKEND_URL}/api/:path*`; and `/api/health` is defined on the **backend** (`main.py:473`). So a dead backend makes the proxied health-check fail → Railway restarts. The "reports healthy while the API is down" scenario cannot occur.

**What remains true:** both processes share one container, so a container-level OOM takes both down and they can't be scaled independently. That's a legitimate design limitation — but it's a *scaling* point, not the *reliability* failure the review describes. Severity: 🟢 low, not critical.

### 2. No Database Attached

> **Original claim:** The app runs in in-memory mode; every session, score, account, cohort, audit log is in RAM and permanently lost on any restart.

**🔍 Evaluation — 🟠 Overstated, but this is where the one real action lives.**

The code no longer *defaults* to memory, and actively resists it:
- `main.py` selects the store as: `USE_MEMORY_DB` → memory; else Postgres if reachable; else memory (`main.py:163-178`). **Both memory paths call `_refuse_memory_db_in_prod()`, which `sys.exit(1)`s in production** unless `ALLOW_MEMORY_DB_IN_PROD=true`. An accidental memory-mode prod deploy fails loudly instead of silently losing data.
- Facilitator-configured state (cohort settings, briefing-video URLs, templates, registry, audit, the memory snapshot) is **already durable** on the Railway volume via `MURESSONS_DATA_DIR` — see `DEPLOYMENT_CHECKLIST.md §2`. So "audit logs / cohort configs / facilitator accounts lost on restart" is **not** accurate once the volume is mounted.

**What is genuinely true:** the *live* instance is running in the memory escape-hatch (no Postgres attached), so **game sessions, player round-state, and CEO-interview scores are volatile**. That is worth fixing — but it's a deployment configuration gap, not an architectural flaw. The recommendation ("attach PostgreSQL") is correct; the framing ("all data permanently lost, unavoidable") is not.

> ⚠️ **Gap the review missed (and so does the repo's own checklist):** the base tables (`sessions`, `global_round_states`, `bu_round_states`, `decision_audit_log`) are created by `db/init.sql`. The local compose stack auto-applies it via `/docker-entrypoint-initdb.d`, but **Railway's managed Postgres will not run it.** `database.get_pool()` immediately issues `ALTER TABLE sessions …` (`database.py:32`) — against a database with no `sessions` table that raises `relation "sessions" does not exist` and the container crashes on boot. **You must apply `init.sql` to the Railway database once before switching.** See the cutover steps.

### 3. Secrets Baked into the Dockerfile

> **Original claim:** `MASTER_PASSWORD`, `JWT_SECRET`, `PROJECT_ADMIN_PASSWORD` are hardcoded as `ENV` lines in the Dockerfile.

**🔍 Evaluation — ❌ False (already removed).**

The Dockerfile's only `ENV` line is `ENV PORT=3000`. There are no secret `ENV`s, and an explicit `SEC-2` comment forbids baking even `USE_MEMORY_DB`. Secrets are read from the environment at runtime and documented in `DEPLOYMENT_CHECKLIST.md §1` as Railway Variables. `main.py` also *fails to boot* in production if `JWT_SECRET` is unset (`SEC-6`, `main.py:131-140`).

**Residual, real:** the burned dev secrets (`sim2026@iim`, `simadmin2026@`) are in git history and must be treated as public — rotate/leave-unset (already flagged in `DEPLOYMENT_CHECKLIST.md §3`). But that's history hygiene, not "secrets baked into the current image."

---

## 🟡 Significant Problems (original)

### 4. Giant Monolithic Files — ✅ Valid (numbers slightly off)

Real line counts: `admin_router.py` **10,505** (not 11,758), `router.py` **6,310** (not 6,557), `database.py` **1,344**, `database_memory.py` **1,342** (not ~2,000). The exact figures are inflated, but the point stands: these files are too large and should be split into domain sub-routers. There's already a `router_split_walkthrough.md` in the repo, so this is on the team's radar. Severity 🟡 confirmed — maintainability, not correctness.

### 5. Dual Database Backends — ✅ Valid

`database.py` (asyncpg/Postgres) and `database_memory.py` (dict-backed) are genuinely parallel implementations (~1,342 lines each) with a documented history of parity fixes. Real maintenance tax and a real source of mode-specific bugs. Legitimate long-term refactor target; not urgent for go-live.

### 6. No CI/CD Pipeline Active — 🟠 Conclusion plausible, reason wrong

The stated reason ("the workflow file isn't present") is **false** — `.github/workflows/ci.yml` exists (2,234 bytes) and `DEPLOYMENT_CHECKLIST.md §4` documents it running pytest + jest. The *plausible* underlying truth: it may not be enforced on GitHub yet — it needs branch-protection to require the checks, **and** it wasn't included in the most recent push (the deploy token lacked the `workflow` scope), so confirm the workflow is actually present on the GitHub default branch and that branch protection requires it. Action: verify on GitHub, add branch protection.

### 7. No CORS Origin Configured — ❌ Largely incorrect for this architecture

- CORS **is** configured: `CORS_ORIGINS` env var with a localhost default, plus auto-append of `https://$RAILWAY_PUBLIC_DOMAIN` (`main.py:362-368`), and an explicit method/header allowlist with `allow_credentials=True`.
- More fundamentally, the login-cookie failure mode described **can't happen here**: the browser only ever talks to the **frontend** origin, and `/api/*` is proxied to the backend **server-side** by Next.js rewrites. From the browser's perspective the API is **same-origin**, so `Set-Cookie` is first-party and CORS does not gate it. CORS would only matter if a browser called the backend cross-origin directly, which this deployment never does.

Severity: 🟢 not a real risk as configured. (Do still set `CORS_ORIGINS` explicitly for defence-in-depth — it's cheap.)

---

## 🟢 What's Done Well — ✅ Agreed

The original's "done well" table is accurate: JWT + HttpOnly cookies, 6-tier RBAC, boot-time security preflight (it's stronger than described — it hard-fails on missing `JWT_SECRET`, memory-DB-in-prod, and insecure cookies), bcrypt, CSP headers (defined in both `next.config.mjs` and a backend middleware), structured logging with request IDs. One correction: the test suite is now **≈1,083 test functions across 80 files**, not 491.

---

## 📋 Corrected Fix Priority

**Do now (operational — this is the real list):**
1. Provision PostgreSQL on Railway, **apply `db/init.sql` to it once**, set `DATABASE_URL`, remove `ALLOW_MEMORY_DB_IN_PROD`, set `JWT_SECRET`. Full steps below.
2. Confirm the durable volume is mounted (`GET /health` → `"durable_storage": true`) — likely already done.
3. Verify `ci.yml` is on the GitHub default branch and required by branch protection.

**Already done — do NOT re-do:** secrets out of the Dockerfile (#3), frontend restart loop + backend-aware health-check (#1), CORS auto-config (#7), memory-DB-in-prod boot guard (#2).

**Backlog (maintainability, not blocking):**
4. Split `admin_router.py` / `router.py` into sub-routers (`router_split_walkthrough.md` already scopes this).
5. Reduce the `database.py` / `database_memory.py` duplication.
6. (Optional, later) Separate front/back into two Railway services for independent scaling.

---

## 🚀 Railway PostgreSQL Cutover — exact steps

> Goal: move the live deployment off the volatile in-memory store onto durable Postgres. Do this in a maintenance window — a deploy/restart drops any in-memory sessions currently in flight.

**1. Add the database**
Railway → your project → **+ New → Database → Add PostgreSQL**. Railway provisions it and exposes a `DATABASE_URL` (Postgres connection string) on the database service.

**2. Create the schema (the step the checklist omits — required)**
Railway's managed Postgres does **not** run `db/init.sql` automatically. Apply it once. Easiest from your own machine with the repo checked out:
```bash
# Copy the database's public connection string from Railway → Postgres → "Connect"
psql "postgresql://<user>:<pass>@<host>:<port>/<db>" -f db/init.sql
```
(Or use Railway's built-in database "Query"/psql console and paste the contents of `db/init.sql`.) You should see `CREATE TABLE` × 4 (`sessions`, `global_round_states`, `bu_round_states`, `decision_audit_log`) plus the immutability triggers.

**3. Point the app service at it (Railway → app service → Variables)**
| Variable | Value |
|---|---|
| `DATABASE_URL` | reference the Postgres service's `DATABASE_URL` (Railway lets you set `${{Postgres.DATABASE_URL}}`) |
| `USE_MEMORY_DB` | `false` |
| `ALLOW_MEMORY_DB_IN_PROD` | **delete this variable** (this is the "flip off the memory override") |
| `JWT_SECRET` | a fixed value — generate with `openssl rand -hex 32` (must be set or prod boot fails; keep it stable or all logins invalidate) |
| `MURESSONS_DATA_DIR` | your volume path, e.g. `/data` (leave as-is if already set) |
| `CORS_ORIGINS` | `https://mayen-production.up.railway.app` (defence-in-depth) |
| `DEBUG` | `false` |

**4. Redeploy** (Railway auto-redeploys on a variable change; otherwise trigger a deploy).

**5. Verify from the boot log** (Railway → Deploy logs):
- `[POSTGRES] PostgreSQL mode` — **not** `[MEMORY]`.
- No `SEC-2 FATAL` / `SEC-6 FATAL` banners.
- No `relation "sessions" does not exist` (that means step 2 was skipped).

**6. Verify from the API:**
```
GET https://mayen-production.up.railway.app/health
```
Expect `"database": "postgres"` (not `"memory"`) and `"durable_storage": true`.

**7. End-to-end proof:** create a facilitator account, redeploy, confirm it still logs in. That is the exact durability the change buys you.

> **Rollback:** if the Postgres boot fails, set `ALLOW_MEMORY_DB_IN_PROD=true` again to bring the app back on the in-memory store while you debug the schema step — the app returns to its current behaviour immediately.
