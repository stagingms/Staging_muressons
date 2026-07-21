# Railway Login & Deployment Fix — Muressons

**Symptom:** the sim runs perfectly locally, but on Railway you cannot log in —
passwords are "not recognized."

**This is not a code bug. It is three pieces of Railway configuration that the
code deliberately depends on and that don't exist by default.** Work through the
steps below in order; the whole thing is ~15 minutes.

---

## 1. Why login breaks (the one-paragraph version)

Your facilitator accounts do **not** live in the database schema. They live in a
flat file, `db/facilitator_registry.json` (≈147 KB of accounts + bcrypt hashes).
That file is *intentionally* excluded from the Docker image by `.dockerignore`
(shipping a developer's local accounts into production is its own bug), and
Railway's container filesystem is **ephemeral**. So unless a persistent **Volume**
keeps that file alive, every deploy starts with an **empty registry** — and the
app falls back to a single `FAC-EMERGENCY` account whose random password is *not
printed to logs in production*. None of your local logins exist, so every one is
rejected.

On top of that, your secrets file `backend/.env.railway` is **gitignored *and*
dockerignored** — it never reaches Railway. Every variable in it has to be pasted
by hand into Railway → Variables.

---

## 2. Set the environment variables  (Railway → your service → **Variables**)

Use the values you already recorded in `backend/.env.railway` (or generate fresh
ones with the commands shown). Do **not** rely on the file being read — paste each
key/value into the Railway UI.

| Variable | Value | Notes |
|---|---|---|
| `USE_MEMORY_DB` | `false` | Forces the durable Postgres path. |
| `JWT_SECRET` | *(your 64-hex value)* | **Mandatory.** Without it + `DEBUG=false`, the backend `exit(1)`s at boot and crash-loops (SEC-6). Generate: `openssl rand -hex 32`. |
| `JWT_EXPIRY_HOURS` | `8` | Covers a full-day workshop. |
| `MASTER_PASSWORD` | *(your value)* | god_mode break-glass login (id: `god_mode`). **This is your way back in** while the registry is empty. Generate: `openssl rand -base64 24`. |
| `PROJECT_ADMIN_PASSWORD` | *(your value)* | project_admin provisioning login. |
| `MURESSONS_DATA_DIR` | `/data` | Where the registry + mutable state persist. **Only works if a Volume is mounted here — see step 4.** |
| `TRUSTED_PROXY_IPS` | `127.0.0.1,::1,10.0.0.0/8,100.64.0.0/10` | Without this, every student shares one rate-limit bucket behind Railway's edge — one mistyped password can 429 the whole cohort. |

**Leave unset** (their safe defaults matter): `DEBUG`, `PLAYER_MASTER_PASSWORD`,
`ALLOW_MEMORY_DB_IN_PROD`, `ALLOW_INSECURE_COOKIES`, and `DATABASE_URL` (Railway
injects that one automatically in the next step).

---

## 3. Attach PostgreSQL

Railway project → **New → Database → PostgreSQL**. Then, on your app service,
make sure `DATABASE_URL` is referenced (Railway usually wires it automatically;
if not, add a variable reference to the Postgres service's `DATABASE_URL`).

You do **not** set `DATABASE_URL` by hand.

---

## 4. Mount a Volume at `/data`  (this is the step that actually fixes login)

App service → **Settings → Volumes → Add Volume**, mount path **`/data`**.

- The path **must match `MURESSONS_DATA_DIR`** from step 2 (`/data`).
- **Do NOT mount it over `/app/db`** — that would hide the seed/config files that
  ship in the image and break the app in a different way.

Without this volume, steps 2–3 still leave you with an empty registry on every
redeploy. This is the single most important step.

---

## 5. Redeploy, then read the logs

After redeploy, the boot logs should contain:

```
[preflight] Deployment configuration looks correct.
[POSTGRES] PostgreSQL mode
```

If instead you see a `SEC-6 FATAL` (JWT_SECRET), `SEC-2 FATAL` (memory DB in
prod), or a `DEPLOYMENT PREFLIGHT` warning block — the log line names the exact
missing piece. That block is the fastest way to confirm the fix landed.

---

## 6. Getting in the first time + restoring your accounts

Right after the fix, the registry on the fresh volume is still empty. Two ways in:

1. **Log in as god_mode** — facilitator id `god_mode`, password = your
   `MASTER_PASSWORD`. From there you can recreate facilitators (they now persist,
   because the volume is mounted). This is the clean path.

2. **Restore your existing registry** — your local
   `db/facilitator_registry.json` holds all your real accounts. Copy it onto the
   volume at `/data/facilitator_registry.json` (Railway shell, or a one-off
   deploy that writes it), then redeploy. On boot you should see
   `[persistence] Restored N facilitator(s) from registry.`

   ⚠️ Do **not** also copy `master_password.json` onto the volume — if a rotated
   override file exists there, it silently *wins* over your `MASTER_PASSWORD`
   variable, which recreates the exact "password doesn't work, nothing explains
   why" symptom. (Your local `db/` doesn't currently have one, so you're fine —
   just don't introduce it.)

---

## Notes on the architecture review you received

Two of its three "critical" items are already handled in your current code:

- **"No CI/CD — tests never run"** — outdated. `.github/workflows/ci.yml` exists
  and runs backend pytest + frontend jest + `next build` on every push and PR.
  The only remaining step is a GitHub UI action: **Settings → Branches → add a
  branch protection rule** requiring those checks to pass before merge.
- **"No database — all data in RAM"** — this is a *provisioning* gap (steps 3–4
  above), not a code gap. The code already defaults to Postgres and *refuses to
  boot* on in-memory storage in production.
- **"Frontend has no restart loop"** — this one was real. **Fixed in code** — see
  the patched `docker-start.sh` delivered alongside this checklist; commit and
  redeploy to pick it up.
