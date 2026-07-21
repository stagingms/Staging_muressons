# Muressons — Railway Deployment Checklist

Deploy-on-push means whatever reaches the deploy branch ships. Run this list
before pointing live participants at the app. It covers the ops-side items from
the 2026-07-16 QA review (#8) that are configuration, not code — plus the two
runtime gates (#9, #10) that need a staging environment.

> A `git push` to the deploy branch **restarts the container**. Do not push
> during a live session.

---

## 1. Environment variables (Railway → Service → Variables)

| Variable | Set to | Why |
|---|---|---|
| `USE_MEMORY_DB` | `false` | In-memory mode loses every session on restart. Prod boot hard-fails on memory unless overridden (SEC-2). |
| `DATABASE_URL` | your Postgres URL | Durable game state. |
| `JWT_SECRET` | `openssl rand -hex 32` | Without it, every login cookie is invalidated on each restart. Prod boot **fails** if unset (SEC-6). |
| `JWT_EXPIRY_HOURS` | `8` (or longer) | Default is **2h** — facilitators get logged out mid-workshop otherwise (QA §6.5). |
| `MASTER_PASSWORD` | a fresh strong secret, **or leave unset** | god_mode break-glass. QA #1 removed the code default: unset = disabled (safe). If set, rotate away from the burned `sim2026@iim`. |
| `PROJECT_ADMIN_PASSWORD` | fresh secret or unset | project_admin (provisioning-only). Unset = disabled. Rotate away from burned `simadmin2026@`. |
| `PLAYER_MASTER_PASSWORD` | usually unset | Optional player master-unlock; keep disabled unless support needs it. Must differ from `MASTER_PASSWORD`. |
| `MURESSONS_DATA_DIR` | the volume mount path, e.g. `/data` | QA #3: keeps facilitator registry / token versions / bans / audit / master-override / virtual-account profiles **and the game-state snapshot** — every cohort's settings overlay (pacing, briefing-video URLs, templates, analytics visibility) — across redeploys. |
| `CORS_ORIGINS` | your frontend origin(s) | Comma-separated allowlist. `RAILWAY_PUBLIC_DOMAIN` is auto-appended. |
| `TRUSTED_PROXY_IPS` | Railway edge IP(s) | So `X-Forwarded-For` (real client IP) is trusted only from the platform proxy, not spoofable clients (QA #7 depends on this being correct). |
| `WEB_CONCURRENCY` | leave `1` for now | >1 requires the multi-worker gate below (QA #10). `scale_preflight` clamps to 1 without Postgres anyway. |

## 2. Durable volume (QA #3 — required)

Create a Railway **Volume** and mount it at its **own** path (e.g. `/data`),
then set `MURESSONS_DATA_DIR=/data`.

- Do **not** mount it over `/app/db` — that would hide the seed/config files
  baked into the image. The code deliberately reads seeds from `<repo>/db` and
  only the *mutable* files from `MURESSONS_DATA_DIR`.
- On first boot with a fresh volume, existing repo-`db/` copies of the mutable
  files are migrated across automatically (see `backend/runtime_paths.py`).
- **Verify the volume is live two ways:**
  1. Boot log shows `[storage] data dir: /data (configured=True, writable=True,
     railway=True, durable=True)`. If instead you see the `[!!] RAILWAY DETECTED
     WITHOUT A DURABLE DATA DIRECTORY` banner, the volume isn't mounted /
     `MURESSONS_DATA_DIR` isn't set.
  2. `GET /health` returns `"durable_storage": true` (and a `storage` object with
     the details). This is the fastest post-deploy confirmation.
- End-to-end proof: create a facilitator (or set a cohort's briefing-video
  URLs), redeploy, confirm the account still logs in and the settings persist —
  this is the exact failure the volume fixes.

## 3. Rotate the burned secrets (QA #1)

`sim2026@iim` and `simadmin2026@` are in git history — treat them as public.
Set fresh values (or leave the break-glass disabled). Never reuse the old ones.

## 4. CI branch protection (QA §4.1)

`.github/workflows/ci.yml` runs pytest + jest on every push/PR, but a red run
only **blocks merge** once branch protection requires the check:

GitHub → Settings → Branches → add a rule for the deploy branch →
require the `Backend — pytest` and `Frontend — jest` status checks to pass.

## 5. Boot-log sanity check (first deploy)

Tail the deploy logs and confirm:

- `[POSTGRES] PostgreSQL mode` (not `[MEMORY]`).
- No `SEC-2 FATAL` / `SEC-6 FATAL` banners.
- `[SEC-4] MASTER_PASSWORD not set — ... DISABLED` **or** the `SEC-4 WARNING`
  armed banner — whichever you intend.

---

## Runtime gates that still need a staging pass (cannot be done from code)

### QA #9 — UX + accessibility pass
Run `load_tests/UX_VERIFICATION_CHECKLIST.md` against a staging deploy in a real
browser: facilitator intervene in ≤2 clicks, all-teams-at-a-glance, player board
usable without horizontal scroll at 1280/1366/1440, draft-survives-refresh. Then
an axe / `accessibility-review` pass on the player board and facilitator
dashboard (contrast of danger/success deltas, keyboard reach of the commit CTA).
Fix whatever fails before go-live.

### QA #10 — multi-worker scale gate (only before a multi-classroom / ~500-user event)
Prerequisite: fixes #4, #5, #6 (done) so shared state is coherent across workers.
On a Postgres staging deploy with `WEB_CONCURRENCY≥2`:

1. `load_tests/split_brain_probe.js` — confirm a facilitator freeze/pacing/tunable
   change propagates to players on **all** workers (the coordination store +
   the #5 publishes are what make this pass).
2. `load_tests/throughput_test.js` — ramp to 100 cohorts × 5 players; watch p95
   `/dashboard` and `/commit-turn` latency and the 409/429 rate.

Only enable `WEB_CONCURRENCY>1` and Railway replicas after both pass. Note: the
WebSocket fan-out is still per-process (QA §1.4) — until pub/sub is added,
cross-worker pushes fall back to the 5–15s client polling, so verify that
latency is acceptable for your session.
