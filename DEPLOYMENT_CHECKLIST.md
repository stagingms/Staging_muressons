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
     mounted=True, railway=True, durable=True)`. `mounted` is read from
     `/proc/mounts` (OPS-3, audit 2026-09-04): the image sets
     `MURESSONS_DATA_DIR=/data` and creates the directory, so `configured` and
     `writable` are true **with no volume attached** — only `mounted=True`
     proves the volume is there. If you see the `[!!] … IS NOT A MOUNTED
     VOLUME` banner the directory is on the container filesystem and every
     redeploy wipes it; the `[!!] RAILWAY DETECTED WITHOUT A DURABLE DATA
     DIRECTORY` banner means `MURESSONS_DATA_DIR` isn't set at all.
  2. `GET /health` returns `"durable_storage": true` and
     `"storage": {"mounted": true, "mount_point": "/data", …}`. This is the
     fastest post-deploy confirmation. (`"mounted": null` means the platform
     exposes no mount table; then rely on the end-to-end proof below.)
- End-to-end proof: create a facilitator (or set a cohort's briefing-video
  URLs), redeploy, confirm the account still logs in and the settings persist —
  this is the exact failure the volume fixes.

### 2b. Volume free space (A6, 2026-08-04)

`writable: true` is written with a 2-byte probe, so it stays true with
kilobytes left. A full volume therefore used to be invisible until a pack
upload or a registry write failed **mid-class**, with every health signal green.

`GET /health` now also reports:

```json
"low_disk_space": false,
"storage": { "free_bytes": 48210739200, "total_bytes": 53687091200, "free_pct": 89.8, "low_space": false }
```

- `low_disk_space` trips under **10% free OR under 100 MB**, whichever comes
  first — percentage alone is meaningless on a large disk, bytes alone on a
  small volume.
- If the platform refuses to report usage, the `free_*` keys are **absent** and
  `low_space` stays `false`. Absence means *unknown*, not *healthy* — alert on
  `low_disk_space == true`, and treat missing keys as a probe to investigate,
  not an all-clear.
**Alerting on it — use `?strict=1`.** Railway's own healthcheck only reads the
status *code*, and `/health` deliberately returns **200** even on a low volume:
a failing healthcheck RESTARTS the container, which fixes nothing and takes a
live workshop down. So the failure is opt-in.

```
GET /health?strict=1   →  200 normally
                       →  503 + {"status":"degraded"} when low_disk_space
                       →  503 + {"status":"degraded","database_reachable":false,
                                 "database_error":"…"} when Postgres does not
                                 answer SELECT 1 within 2 s (OPS-4)
```

`?strict=1` is the only call that touches the database: the plain `/health`
(Railway's healthcheck, the facilitator RunBar dot) stays a no-I/O 200, so a
database outage is visible to your monitor without restarting the container.

Point any uptime monitor (UptimeRobot, Better Stack, Healthchecks.io — all have
free tiers) at **`https://<your-domain>/health?strict=1`** with a 5–15 minute
interval and the default "alert when not 200" rule. No JSON/keyword support
needed. Disks fill slowly; a 15-minute interval is ample.

Do **not** point Railway's `healthcheckPath` at the strict URL — that is the
restart loop this design avoids. Leave it on `/api/health`.

## 3. Deploy gating — do not let a push ship mid-class (A4)

Deploy-on-push means any commit to the deploy branch restarts the container
under a live workshop: ~1–2 minutes of downtime plus stale JS in every open
tab. Two ways to close this; pick one.

**Preferred — a `production` branch Railway watches.**

1. Railway → service → Settings → **Source** → set the deploy branch to
   `production`.
2. Day-to-day work continues on `main`; CI still runs on every push.
3. Ship deliberately, never during a session:
   ```
   git checkout production && git merge --ff-only main && git push origin production
   git checkout main
   ```
   `--ff-only` is the point: it refuses if `production` has drifted, rather
   than creating a surprise merge commit that ships something untested.

**Simpler — disable auto-deploy.** Railway → service → Settings → turn off
**Auto Deploy**, then press *Deploy* by hand. Fewer moving parts, but nothing
records *what* was deployed or when, so prefer the branch if you can.

Either way, also require the CI checks (§4) so a red build cannot reach the
deploy branch in the first place.

## 3b. Rotate the burned secrets (QA #1)

`sim2026@iim` and `simadmin2026@` are in git history — treat them as public.
Set fresh values (or leave the break-glass disabled). Never reuse the old ones.

## 4. CI branch protection (QA §4.1)

`.github/workflows/ci.yml` runs pytest + jest on every push/PR, but a red run
only **blocks merge** once branch protection requires the check:

GitHub → Settings → Branches → add a rule for the deploy branch →
require the `Backend — pytest` and `Frontend — jest` status checks to pass.

## 5. Boot-log sanity check (first deploy — and every deploy before a class)

Tail the deploy logs and confirm:

- `[POSTGRES] PostgreSQL mode` (not `[MEMORY]`).
- No `SEC-2 FATAL` / `SEC-6 FATAL` banners.
- `[SEC-4] MASTER_PASSWORD not set — ... DISABLED` **or** the `SEC-4 WARNING`
  armed banner — whichever you intend.
- `[storage] … mounted=True … durable=True` (see §2).
- **No `[CONFIG] WARNING` line and no `[config] CLAMPED …` line.** Each one
  means the `simulation_config.json` on the volume carries a legacy value that
  `config.py` refused: the file says one thing, the engine runs its default.
- `[config] volume config matches the image copy (in_sync)`. If instead you see
  `[config] volume differs from image on N keys: …`, the volume kept the
  config an earlier build seeded and a changed default is **not in effect**
  (this includes keys no clamp guards — e.g. `terminal_valuation.shares_outstanding`).

### 5b. Refresh the volume config (CFG-01/02, audit 2026-09-04)

The data volume keeps its own `simulation_config.json` forever
(`runtime_paths.config_file` seeds it once and never overwrites it), so a
volume created before a build that changed a default silently runs the old
numbers.

**Since CFG-10 (2026-09-06) the boot does the common case itself:** a volume
holding a KNOWN superseded value (the table in `backend/config_migrations.py`
— the pre-launch economy, the 2026-09-03 natural-decay tiers, the 100,000,000
share count) is rewritten to the current value before `config.py` reads it,
announced in the boot log as `[config] MIGRATED <key>: <old> -> <new>` and
listed in `/api/health` under `config.migrated`; a key the image carries and
the volume lacks (seeded by a build that predates the key) is filled with the
image's value and announced as `[config] SEEDED <key> = <value>` (kind
"seeded" in the same list). After such a boot `volume_differs_from_image_on`
is empty and nothing below is needed. A value
that is neither superseded nor current is a deliberate tuning: it is left
alone and keeps showing as `image_vs_volume` — that is the case for the
manual steps below. Do them after any deploy that touched
`simulation_config.json` and left `volume_differs_from_image_on` non-empty,
and before every class:

1. **Inspect** (from a Railway shell, or `railway ssh --`):
   ```
   python3 -c "import json;c=json.load(open('/data/simulation_config.json'));e=c['engine_parameters'];print('cbam',e['cbam']['surcharge_rate'],'imit',e['imitation_decay']['default_rate'],'ratchet',e['regulatory_ratchet']['baseline'],'synergy',e['synergy'].get('max_reduction_per_round'),'ncd',c['ncd_parameters'].get('hard_cap'),c['ncd_parameters'].get('warn_threshold'),c['ncd_parameters'].get('opex_penalty_per_unit'),'shares',c['terminal_valuation'].get('shares_outstanding'))"
   ```
   Expected: `cbam 100 imit 0.05 ratchet 20.0 synergy 0.06 ncd 5000 1000 1000 shares 6500000`.
2. **Patch** anything else with the shipped patcher (it backs the file up first
   and only touches the keys it knows):
   ```
   python3 /app/backend/patch_volume_config.py /data/simulation_config.json
   ```
   or, to adopt the image copy wholesale (loses any deliberate tuning):
   `cp /app/simulation_config.json /data/simulation_config.json`.
3. **Restart** the service (Railway → Deployments → Restart), then re-run
   step 1 and re-check the boot log per §5. As super-admin,
   `GET /api/admin/config/live` must show `"healthy": true` with an empty
   `problems` list — `clamped_value` entries name any key still refused,
   `image_vs_volume` names any key still differing from the image.

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

Only enable `WEB_CONCURRENCY>1` and Railway replicas after both pass, and record
the pass by setting `MURESSONS_MULTIWORKER_VERIFIED=true` in the service
variables: `backend/scale_preflight.py` clamps `WEB_CONCURRENCY` back to 1 at
boot unless that variable is truthy (and `/health` reports it as
`scaling.multi_worker_verified`), so the variable is the gate, not a memo.
Note: the
WebSocket fan-out is still per-process (QA §1.4) — until pub/sub is added,
cross-worker pushes fall back to the 5–15s client polling, so verify that
latency is acceptable for your session. Not run for the 2026-09 cohort:
`WEB_CONCURRENCY=1`.
