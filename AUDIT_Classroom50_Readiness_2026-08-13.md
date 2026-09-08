# Muressons — Pre-Deployment Readiness Audit for a Live 50-Student Session

**Auditor role:** principal engineer / SRE + application security + simulation-design reviewer, last reviewer before go-live.
**Date:** 2026-08-13 · **Repo:** `github.com/mastersustainability/Mayen` (local `main` @ `246c1d7`) · **Method:** read-only static sweep (10 dimensions) + local dynamic probes on a throwaway in-memory instance. No production host was touched.

---

## 1. Verdict

# GO-WITH-CONDITIONS

The code is materially better than a first glance at the tracked `.env` files suggests: git history is clean of real secrets, the store has genuine atomic writes and cross-process commit locking, RBAC is mostly principled, and third-party PII egress is inert by default. It is **not** shippable as-is for a graded, unrepeatable cohort, but every blocker has a cheap pre-class mitigation. It becomes GO **only if the Do-Before-Class list (§3) is completed**. Two blockers dominate: (a) pre-provisioned facilitator/player accounts use a **documented, guessable default password that is not enforced to change**, so a student can sign in as a facilitator or a peer; (b) **two unauthenticated endpoints return the full answer key and every engine tunable** — I pulled both live with no cookie. Both are configuration/one-line-guard fixes, not rewrites. Without them: NO-GO. With them plus the deploy-freeze, secret rotation, JWT-expiry and proxy-IP settings: GO.

---

## 2. Assumptions

Stated explicitly because severity is judged against them, not a generic SaaS:

- **~50 students + 1 facilitator (+ maybe 1 co-facilitator), all live at once.** Facilitator is **not** the developer: cannot read a stack trace, SSH, or patch code. Anything needing developer intervention to recover = an outage.
- **Burst login** ~50 in 5 min; **synchronised commit** ~50 requests in a 60 s window at each of 10 round boundaries.
- **Session 2–4 h, possibly split across two days** → token expiry, resumption, and durability across a restart all in scope (per your answer: plan for both).
- **Network mixed:** most students in one room behind one NAT'd campus/hotel egress IP; a few remote. (Your answer.) I therefore treat any IP-scoped limiter/ban as a whole-room risk.
- **Deployment: Railway, deploy-on-push, from `main`, single Docker image, mounted volume, Postgres (`USE_MEMORY_DB=false`), one worker** (scale_preflight forces 1). (Your answer: Railway current `main`.)
- **Privacy: India DPDP Act + general institutional best practice.** (Your answer.)
- **Unrepeatable exec-ed cohort; output used for debrief and possibly grading** → determinism and fairness are first-class, not nice-to-haves.

**Could not verify (need you / cloud access):** the actual Railway service branch and env-var values; whether the room is truly one egress IP; whether play is **per-player** or **per-team** commit (this changes F09 severity materially); real device/browser matrix; live redeploy behaviour on open tabs.

---

## 3. Do-Before-Class list

Ordered by impact ÷ effort. Each is executable by a non-developer unless marked **[dev]**. IDs trace to §5.

1. **[dev, 10 min] Add an auth guard (or edge-block) to the answer-key endpoints** `GET /api/admin/simulation-reference`, `/engine-tunables`, `/scenario-presets`. → **F02**. If no dev is available before class, block those three paths at the Railway edge/proxy and confirm they 401/404.
2. **[5 min] Every facilitator and co-facilitator logs in and changes their password now; delete every unused facilitator account.** Closes the `FAC-NNN@321` window. → **F01**.
3. **[5 min] Create player accounts just-in-time and have each student change password on first supervised login; watch the audit log for logins to not-yet-arrived IDs.** → **F08**.
4. **[5 min] In Railway → Variables set fresh, distinct secrets:** `JWT_SECRET=$(openssl rand -hex 32)`, strong distinct `MASTER_PASSWORD` and `PROJECT_ADMIN_PASSWORD`, **leave `PLAYER_MASTER_PASSWORD` unset**, and set **`JWT_EXPIRY_HOURS=10`** (covers a two-day gap only if the same day-1 token isn't expected to survive overnight — see F05). Do **not** paste the dev `.env`. → **F03, F05**.
5. **[3 min] Set `TRUSTED_PROXY_IPS`** to Railway's edge CIDRs (the value is in `.env.railway.example`, incl. `10.0.0.0/8,100.64.0.0/10`). Without it, 50 students collapse into one rate-limit bucket and a room-wide ban can persist. → **F10**.
6. **[2 min] Freeze deploys for the session.** Disable auto-deploy or pin the service to a release tag; do not push anything (even docs) while class is live. → **F06, F16**.
7. **[1 min] Do not select the `un_sdg` paradigm.** It has no round 6–10 config and dead-ends the cohort at round 6. Use `legacy_abc`, `advanced_climate`, `healthcare`, or `multi_toggles`. → **F07**.
8. **[2 min] Per cohort, set `redact_peer_identities=true` and set a one-line `consent_text` (with `consent_required=true`).** → **F14, F17**.
9. **[dev, 5 min] Confirm the deployed build.** Check `/api/health` → `build.commit` equals `git rev-parse main`; if it's `null`, set `RAILWAY_GIT_COMMIT_SHA` so you can. Confirm the service branch is `main` not `production` (they diverge by 8 commits incl. a currency-rate guard). → **F13**.
10. **[dev, 15 min] Raise `DB_MAX_CONNECTIONS`** to ≥ 2× (concurrent cohorts on the instance), confirm Railway Postgres `max_connections` is higher, and **advance cohorts one at a time** so commit bursts don't overlap. → **F09**.
11. **[10 min] Pre-flight dry run:** boot a throwaway cohort in the chosen paradigm, play to round 10 with 2 accounts, reload mid-commit once, and confirm the decision panel is never empty and the debrief numbers tie. → **F07, F11, F12, F18**.
12. **[after class, 5 min] Purge the cohort** with `DELETE /api/admin/players` and rotate `MASTER_PASSWORD` — Postgres will not auto-reap. → **F19**.

---

## 4. How to read the findings

≤20 findings, ranked by classroom impact. `CONFIRMED` = I read the path end-to-end or demonstrated it live; `PLAUSIBLE` = reasoned but not demonstrated (with what would settle it). Severity is classroom impact (P0 = class-stopper / student reaches admin / silent data loss; P1 = strands individuals, corrupts results, or forces a briefed workaround; P2 = fix before next cohort; P3 = hygiene).

---

## 5. Findings

### F01 — Pre-provisioned accounts use the documented default `FAC-NNN@321`; `must_change_password` is a response flag, never enforced → a student can sign in as a facilitator
**P0 · CONFIRMED (mechanism) / PLAUSIBLE (exploit window) · D2/D3**

- **Evidence:** `backend/default_credentials.py` → `default_facilitator_password()` returns `f"{facilitator_id}@321"` (also documented in `CLAUDE.md`). Login issues the token and cookie before returning the flag: `backend/admin_router.py:2662-2668` (`create_facilitator_token` + `set_session_cookie`), `must_change_password` returned only as a body field at `:2686`. `grep must_change_password backend/*.py` shows **no guard** ever rejects a request when it's true. Facilitator IDs are sequential (`FAC-{max_id:03d}`, `admin_router.py:2210-2219`).
- **Failure scenario:** A co-facilitator account `FAC-002` is provisioned but not yet logged in. A student submits `FAC-002` / `FAC-002@321`, receives a valid HttpOnly facilitator JWT, and can advance rounds, fire shockwaves, reveal credentials, or lock the real facilitator out by changing the password.
- **Why it matters at 50:** One student silently owns the run; the non-developer facilitator has no symptom until the class is already derailed. This is the "student reaches admin capability" case the rubric calls P0.
- **Fix (server-side enforcement):**
  ```diff
  # admin_router.py, in the privileged dependency (require_facilitator/require_sim_manager)
  + if principal.must_change_password:
  +     raise HTTPException(403, "Password change required before using this account.")
  ```
  Issue only a change-password-scoped token until the flag clears.
- **Cheaper pre-class mitigation:** every facilitator logs in and changes password before students arrive; delete unused facilitator accounts (Do-Before-Class #2).
- **Falsification attempted:** searched for any middleware/guard reading the flag (none) and whether the token is withheld until change (it is not). Exploit needs an un-activated account to exist and the student to know the `@321` convention — hence CONFIRMED mechanism, PLAUSIBLE window. Mitigation fully closes it.

### F02 — Two unauthenticated endpoints return the full answer key and every engine tunable (pulled live, no cookie)
**P1 · CONFIRMED (demonstrated live) · D3**

- **Evidence:** `admin_router.py:1437` `get_simulation_reference()` — no `Depends` — returns per-round `treasury`/`ci_delta`/`reputation_delta`/`ncd_delta`/`slo_delta`/`flags` for all 10 rounds and crisis text. `admin_router.py:10336` `get_engine_tunables()` and `:10560` `get_scenario_presets()` — no guard — return every constant (`overrun_probability`, `greenwashing_penalty`, `dividend_cut_threshold`, `lockin_streak_threshold`, `fog_of_war_rounds`, …). Demonstrated:
  ```
  $ curl -s http://127.0.0.1:8099/api/admin/simulation-reference   → HTTP 200, full payoff matrix
  $ curl -s http://127.0.0.1:8099/api/admin/engine-tunables         → HTTP 200, {"tunables":{"overrun_probability":0.25,...}}
  ```
- **Failure scenario:** one student runs `curl https://<host>/api/admin/simulation-reference`, gets the optimal choice for every round, and shares the JSON.
- **Why it matters at 50:** destroys the pedagogical/graded validity of the whole cohort's exercise — and it's trivially scriptable from any student device.
- **Fix:** add `_g: None = Depends(require_facilitator)` to all three handlers.
- **Cheaper pre-class mitigation:** edge-block the three paths and verify they 401 before students join.
- **Falsification attempted:** confirmed no router-level dependency on `admin_router` (`main.py` mounts it per-route), and the functions take no gating parameter. Fully open. (Note: the previously-reported `esg_profile_weights` leak **is** fixed — `admin_router.py:421-434` gates it — so these three are the live gap, not that one.)

### F03 — Secrets must be set fresh and distinct in Railway; the dev values are weak and `PLAYER_MASTER_PASSWORD` is a skeleton key
**P1 · PLAUSIBLE (operator-dependent) · D2**

- **Evidence:** on-disk `backend/.env` (NOT in git — verified 0 commits — and `.dockerignore`d) holds `MASTER_PASSWORD=sim2026@iim`, `PROJECT_ADMIN_PASSWORD=simadmin2026@`, `PLAYER_MASTER_PASSWORD=localplayer2026`, `JWT_SECRET=1a5d3ca3…`. `backend/master_credentials.py:56-63` — `verify_player_master_password()` is a **master key to any student account**; `.env.railway.example` documents it as "DELIBERATELY UNSET IN PRODUCTION." `main.py:147` hard-fails prod boot with no `JWT_SECRET`.
- **Failure scenario:** a non-developer copies the dev `.env` into Railway → `PLAYER_MASTER_PASSWORD=localplayer2026` becomes a live guessable master key to every student; `MASTER_PASSWORD=sim2026@iim` becomes god-mode break-glass.
- **Fix / mitigation (~5 min):** in Railway → Variables set `JWT_SECRET=$(openssl rand -hex 32)`, strong distinct `MASTER_PASSWORD`/`PROJECT_ADMIN_PASSWORD`, leave `PLAYER_MASTER_PASSWORD` unset; confirm the boot log prints `[preflight] Deployment configuration looks correct.`
- **Falsification attempted:** confirmed none of these files are in git history or the image (`.dockerignore` has `**/.env`, `**/.env.*`, explicit `db/jwt_secret.key`). This is a weak/reused-secret risk, not a leak.

### F04 — `/api/health` never checks the database → reports green while Postgres is down (confirmed it never queries the DB)
**P1 · CONFIRMED · D1**

- **Evidence:** `backend/main.py:527-591` reads `_use_memory`, `db.__name__`, and a volume probe, but never runs `SELECT 1` or `db.get_pool()`. Live: the running instance returned `{"status":"ok"}` having issued zero DB queries. Railway healthcheck is `/api/health` (`railway.json`).
- **Failure scenario:** Postgres blips or hits its connection cap at a round boundary; every commit 500s, but `/api/health` stays 200. Railway shows healthy, does not restart or alert.
- **Why it matters at 50:** the one condition the healthcheck should catch (DB unreachable during the commit stampede) is the one it ignores; whole cohort stranded with no platform signal.
- **Fix:**
  ```diff
  + try:
  +     async with (await db.get_pool()).acquire() as c:
  +         await c.execute("SELECT 1")
  + except Exception:
  +     return JSONResponse({"status":"degraded","database":"unreachable"}, status_code=503)
  ```
- **Mitigation:** runbook — if commits fail across the room, restart the Railway service manually (it will not self-heal on this signal).
- **Falsification attempted:** searched for any DB touch in the health path or a separate readiness route — none; the only DB touch at boot is `lifespan`.

### F05 — Default JWT TTL is 2 h; a 2–4 h (or two-day) session expires the facilitator mid-class and cannot self-refresh
**P1 · CONFIRMED · D3**

- **Evidence:** `auth_jwt.py:58` `JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS","2"))`; cookie `max_age` tracks it (`:208`). `/auth/refresh` is itself behind `require_facilitator` (`admin_router.py:2758`) → once expired it 401s, so an expired session can only be re-logged-in, not refreshed. The committed `.env.railway.example` sets `=8`, but Railway uses dashboard vars, not the file.
- **Failure scenario:** dashboard var unset → facilitator cookie expires ~2 h into the session; every privileged action 401s and they must re-enter the master/facilitator password mid-class in front of the room. (Players degrade gracefully to REST polling, so only facilitators are stranded.) A two-day split makes this near-certain.
- **Fix / mitigation:** set `JWT_EXPIRY_HOURS` in Railway to session-length + buffer (e.g. 10) and re-login at the start of day 2; verify in a dry run that the facilitator can still act after 2 h.
- **Falsification attempted:** confirmed refresh is gated by the same expiry it's meant to renew, so there is no silent renewal path.

### F06 — Deploy-on-push has no in-repo gate or branch pin; any mid-class push cycles the container
**P1 · PLAUSIBLE · D1**

- **Evidence:** `railway.json` has no branch/`watchPatterns` key; the deploy branch lives only in the dashboard. `docker-start.sh` cold-starts Next + gunicorn/uvicorn + the PG pool on every swap. No rollback step in `DEPLOYMENT_CHECKLIST.md`.
- **Failure scenario:** anyone pushes any commit (even docs) to the deploy branch during class → Railway rebuilds and swaps; in-flight commit-turns at a round boundary fail during the multi-second cold start; a regression that passes the (DB-blind, F04) healthcheck silently replaces working code, and a non-developer cannot execute the dashboard "redeploy previous" rollback.
- **Fix / mitigation:** disable auto-deploy for class days or pin to a release tag; document the dashboard "redeploy previous deployment" rollback for the facilitator.
- **What would settle it:** the Railway service settings (deploy branch, wait-for-CI, PR-only deploys) — I cannot see them from the repo.

### F07 — `un_sdg` paradigm has round configs only for rounds 1–5 → selecting it dead-ends the whole cohort at round 6
**P1 · CONFIRMED · D6**

- **Evidence:** `un_sdg` is selectable (`paradigm_registry.py:48`, `VALID_PARADIGMS`). `SDG_ROUND_CONFIGS` defines keys `[1,2,3,4,5]` only (`side_tracks/corporate_sdg/configs.py`); `get_sdg_round_config(6..10)` returns `None` (`:364`), and the provider has **no** legacy fallback (contrast `_pillar` at `paradigm_registry.py:40`). Parity check (run by the sim worker): `un_sdg missing: [6,7,8,9,10]`; the other four paradigms are complete 1–10. Solo pre-seed drops the empty rounds (`router.py:1517 if rcfg:`), so the decision panel — commented "never empty" (`router.py:1508`) — is empty for r6–10.
- **Failure scenario:** facilitator picks UN-SDG; play is normal through round 5, then round 6 shows no options and cannot advance. The cohort's afternoon and any grade basis are gone.
- **Why it matters:** unrepeatable session; the existing test masks it (`test_paradigm_registry.py:39` asserts `None == None`, which passes).
- **Fix:** give `_sdg` a legacy fallback like `_pillar`, or hard-block `un_sdg` as a 10-round paradigm at cohort creation; add a positive test that every `VALID_PARADIGM` yields non-None config for rounds 1–10.
- **Cheaper pre-class mitigation:** do not select `un_sdg` (Do-Before-Class #7).
- **Falsification attempted:** considered `un_sdg` may be a 5-round side-track only — but nothing at cohort/session creation prevents choosing it as the main paradigm, and the registry lists it first-class, so the strand is reachable.

### F08 — Player default `MUR-NNN@123` + sequential IDs → peer account takeover during the login window
**P1 · CONFIRMED · D2/D3**

- **Evidence:** `default_credentials.py` → `default_player_password()` = `f"{player_id}@123"`; player IDs are sequential `MUR-NNN`. `router.py:730-811` `player_login` mints a session and returns `must_change_password` only as a client hint — no server block. The tight rate cap is keyed per `player_id` (`router.py:660-661`), so 50 correct single-guesses across distinct IDs never trip a brute-force cap.
- **Failure scenario:** at start, ~50 players are all `MUR-NNN@123`, none activated. A student iterates `MUR-001..050@123`, logs in as peers, submits sabotaging decisions, or changes their passwords to lock them out.
- **Fix:** same server-side `must_change` enforcement as F01; consider opaque (non-sequential) player IDs or per-account join codes.
- **Cheaper pre-class mitigation:** create accounts just-in-time; each student changes password on supervised first login; watch the audit log for logins to not-yet-arrived IDs.
- **Falsification attempted:** confirmed the default hash is bcrypt-verified and grants a real session, and that per-identity rate-limiting does not stop low-volume correct guesses.

### F09 — DB pool exhausts under the synchronised round-boundary commit burst; stranded students get force-committed with defaults
**P1 · CONFIRMED (pattern) / PLAUSIBLE (trigger) · D4**

- **Evidence:** `router.py:2037` `commit_turn` holds an advisory-lock **connection** for the whole commit (released at `:2065`); within it, `fetch_latest_state`/`get_session_info` each `pool.acquire()` **again** from the same pool (`database.py:925-926`, `router.py:245/405`) → ~2 concurrent connections per in-flight commit. `config.py:45` `DB_MAX_CONNECTIONS=40`, `:49` `DB_ACQUIRE_TIMEOUT=10s`. `player_capacity.py:23` `MAX_PLAYERS_CEILING=20` (hard-clamped — verified) → **50 students cannot be one cohort**, so they run as ≥3 cohorts sharing one 40-connection pool. `database.py:328` sized the pool for "one cohort of ≤20." On timeout, laggards are auto-committed with **defaults (Option B, $1/BU)** at facilitator advance (`router.py:425`).
- **Failure scenario:** ~50 commits in 60 s; ~40 grab advisory conns, each needs a 2nd → pool empties → 503s for the 10 s window → laggards silently committed with default decisions = degraded/lost turn.
- **Why it matters at 50:** fires at the exact worst moment the scenario names; facilitator sees only "save failed" and cannot fix it live.
- **Fix:** run the whole commit on the single held connection (don't re-acquire), or use a `pg_advisory_xact_lock` inside one transaction.
- **Cheaper pre-class mitigation:** raise `DB_MAX_CONNECTIONS` to > 2× concurrent sessions (and confirm Railway PG `max_connections`); advance cohorts one at a time so bursts don't overlap.
- **Falsification / what settles it:** if play is **team-based** (only the driver commits), a cohort emits ~8–9 commits and the pool is safe. **Confirm whether commits are per-player or per-team** — this is the single biggest lever on this finding's severity. The pool-hold pattern itself is confirmed by code.

### F10 — Shared-IP login: whole-room 429 ceiling and a persistent IP-scoped ban if `TRUSTED_PROXY_IPS` is left default
**P2 · PLAUSIBLE · D4**

- **Evidence:** `rate_limit.py:34-35` gives `player_login` a per-IP ceiling of 300/60 s plus a per-identity 10/60 s cap (`router.py:660-661`) — the correct shape. **But** `rate_limit.py:110` `TRUSTED_PROXY_IPS` defaults to `127.0.0.1,::1` only; without the Railway edge range, `_resolve_client_ip` never trusts `X-Forwarded-For` and **every student resolves to the proxy IP → one shared bucket**. On breach, a persistent ban keyed `player_login:<ip>` is written to `rate_bans.json` on the durable volume (`:220-221`) and **survives restart**.
- **Failure scenario:** everyone logs in at once behind one NAT; flaky wifi/captive-portal retries brush 300/60 s → whole room 429s and a 60 s room-wide ban persists, re-triggering on the next retry wave.
- **Fix / mitigation:** set `TRUSTED_PROXY_IPS` to Railway's edge CIDRs (documented in `.env.railway.example`); ideally also fail-loud at boot if Postgres is detected but `TRUSTED_PROXY_IPS` is still localhost.
- **Falsification attempted:** the per-identity cap protects individual accounts regardless of IP, and 300 is well above 50 clean logins — so this needs a retry storm **and** the missing env var, hence PLAUSIBLE. (The CIDR-parse bug is already fixed at `_parse_trusted`.)

### F11 — Stuck-student is invisible: an engine exception on commit returns a bare 500, force-advance silently skips that student, and there is no "who hasn't committed / who errored" board
**P1 · CONFIRMED · D9/D7**

- **Evidence:** global handler returns a generic `{"detail":"An internal server error occurred. Please try again."}` (`main.py:493-502`); `process_tick` is called with no local try/except (`router.py:2420`); the force-advance auto-commit swallows per-student exceptions and `continue`s (`router.py:433-434`); the endpoint returns `{"status":"ok"}` unconditionally (`admin_router.py:3538-3542`) and the UI flashes "✅ stragglers auto-committed" on any 2xx (`RoundPacingControl.js:288`). `grep` for `/logs`, `/errors`, `who.?error`, per-student not-committed view in `admin_router.py` → none.
- **Failure scenario:** one student's saved state hits a deterministic engine error; manual commit → bare 500; retry re-crashes; facilitator presses Force-Advance → that student is silently omitted while the screen says everyone advanced. The student is frozen with no facilitator signal.
- **Fix:** wrap `process_tick` and return an actionable 422 with a support code; have force-advance return `advanced`/`failed` lists and render them; add a read-only `GET /api/admin/cohorts/{id}/board` returning per-player `{round, committed?, last_error}`.
- **Cheaper pre-class mitigation:** runbook — after every Force-Advance, re-open **Session Health** (`GET /api/admin/session-health`, which works under Postgres) and confirm every cohort's round ticked up; for a reported "internal server error," Impersonate the student and Undo-Round them one round to let them re-commit.
- **Falsification attempted:** confirmed there is no per-student error surface and no `failed` field in the force-advance response; confirmed the frontend does surface `detail`, so the generic text is exactly what the student sees.

### F12 — In-progress decision draft can be lost on reload (autosave is gated and on a 30 s timer, with no save-on-unload)
**P1 · CONFIRMED · D8**

- **Evidence:** drafts are saved server-side (good, not localStorage) via `page.js:851-858` autosave → `useSimulation.js:574-610`, but the autosave effect returns early unless **both** a decision is chosen **and** allocations are non-empty, and fires only every 30 s; there is no `beforeunload`/`pagehide` flush. Restore depends on a prior save having fired (`saved_round === roundNumber`).
- **Failure scenario:** a student allocates capital and picks an option, then reloads (or a wifi drop reloads the tab) within 30 s → this round's work is gone; a student who allocated but hasn't yet chosen an option is never autosaved at all.
- **Why it matters at 50:** the scenario guarantees a mid-commit reloader and a wifi dropper; several will hit the unsaved window on a graded round.
- **Fix:** flush on `visibilitychange`/`pagehide` via `navigator.sendBeacon`, debounce-save on each field change, and drop the "both fields required" gate so partial drafts persist.
- **Cheaper pre-class mitigation:** tell students not to reload mid-round; if they must, wait for the "saved" indicator first.
- **Falsification attempted:** looked for a localStorage/sessionStorage draft cache or an unload flush — none exists.

### F13 — Deployed branch is unverified and `main` is 8 commits ahead of `production` (including a backend currency-rate guard)
**P2 · PLAUSIBLE · D1**

- **Evidence:** `git rev-list --count production..main` = 8; `backend/tests/test_currency_rate_guard.py` exists on `main` and is **absent on `production`** (verified `git cat-file -e production:… → absent`), so `production` lacks that guard plus the "measure cap cost four rounds" layout fix (`246c1d7`). Nothing in the repo pins which branch deploys. `/api/health` `build.commit` returned `null` on my instance — so the "which build is this?" feature can't answer the question unless `RAILWAY_GIT_COMMIT_SHA` is set.
- **Failure scenario:** if Railway's source is `production`, students run a stale backend missing the currency guard and layout fix; nobody can tell from the running app.
- **Fix / settle:** confirm the Railway service branch is `main`; set `RAILWAY_GIT_COMMIT_SHA` and check `/api/health build.commit == git rev-parse main`.

### F14 — `peer-leaderboard` returns students' real names, unauthenticated, with redaction off by default
**P2 (→P1 if session IDs are guessable) · CONFIRMED (unauth, live) · D10/D3**

- **Evidence:** `GET /api/simulations/{session_id}/peer-leaderboard` (`router.py:4788`) has no `Depends` and never calls `_assert_player_owns_session` (contrast `export-my-data` at `:1745`). `redact_peer_identities` defaults `False` (`:4806`), so it emits every peer's real `player_name` + treasury/reputation/rank (`:4901,4946`). Live: a request with a bogus session id still returned HTTP 200 (route is open); a valid id returns the roster.
- **Failure scenario:** anyone holding/guessing a valid cohort `session_id` (carried in SPA URLs, may appear in logs) pulls the full roster of real names + performance without authenticating — an unauthorized disclosure under DPDP and a reputational issue for paying execs.
- **Fix:** add the owner/facilitator guard used by `export-my-data`, and/or default `redact_peer_identities=True`.
- **Cheaper pre-class mitigation:** set `redact_peer_identities=true` on the cohort (peers show as "Team N") — one setting, no code change.
- **Falsification attempted:** confirmed the handler has no auth dep and the default path returns `player_name`; the P1 escalation depends on session-id guessability.

### F15 — Financial articulation invariants (RE roll-forward, cash waterfall, dividend consistency) fail by design and are never wired into the running engine
**P1 · CONFIRMED · D6**

- **Evidence:** `audit_financial/financial_invariants.py` documents `inv2_re_rollforward` ("FAILS TODAY (plug)"), `inv6_waterfall_closure` ("FAILS TODAY by up to $55M/round"), `inv7_dividends_consistency` ("FAILS TODAY in clamped rounds"); `check_all` (`:75`) runs only inv1/3/4/5 with the failing three commented out. `grep financial_invariants backend/` → **no call sites**; the guard is an offline script the engine never imports. The balance sheet still *balances* (A=L+E) — via a plug into RE/reserves — which hides the break.
- **Failure scenario:** in the debrief you walk a team P&L → cash flow → balance sheet; retained earnings don't tie to `RE_open + NI − dividends`, up to $55M/round of cash is unexplained, and clamped-dividend rounds show equity distribution ≠ cash out. The numbers don't reconcile in front of the room.
- **Why it matters:** the output feeds a debrief and possibly a quantitative grade; books that balance only via an unexplained plug undermine both.
- **Fix:** wire `check_all` into `process_balance_sheet_tick` (log in prod, raise in dev), then remediate the RE bridge, waterfall and dividend clamp so inv2/6/7 can be enabled.
- **Cheaper pre-class mitigation:** don't present the cash-flow waterfall as authoritative in the debrief; lead with treasury/reputation/valuation, which are internally consistent.
- **Falsification attempted:** checked whether even inv1 (A=L+E) runs live — it doesn't (not imported); confirmed the failing invariants are the articulation/cash ones, so "it balances" is true but load-bearing on a plug.

### F16 — Stale-JS after a mid-session redeploy: a dynamic-chunk 404 is caught, but the recovery panel's first button loops
**P2 · CONFIRMED (code path) · D8**

- **Evidence:** ~30 `dynamic(() => import(...))` code-split components including decision-path modals (`page.js:123-154`, e.g. `DoubleMaterialityMatrix`, required before the R2 commit). No `generateBuildId`/`assetPrefix`/service worker/`ChunkLoadError` handler in `next.config.mjs`. `ErrorBoundary` catches it (not a white screen) but lists **"Try Again" first** (`ErrorBoundary.js:34-36`), which re-requests the dead chunk and loops; only the second button "Reload Page" recovers.
- **Failure scenario:** a redeploy mid-session changes chunk hashes; a student's open tab opens a modal for the first time → 404 → ChunkLoadError → student sits on the looping "Try Again."
- **Fix:** add a global ChunkLoadError handler that force-reloads once (guarded via a sessionStorage flag), pin `generateBuildId`, make "Reload Page" primary.
- **Cheaper pre-class mitigation:** freeze deploys during class (same as F06) — this is the biggest single win.
- **Falsification attempted:** confirmed the ErrorBoundary is mounted (no white screen) and that no chunk-error/version recovery exists; live-deploy behaviour not observable without a real redeploy.

### F17 — No privacy notice/consent shown by default, and Postgres cohorts are never auto-purged (indefinite retention)
**P2 · CONFIRMED · D10**

- **Evidence:** consent is off by default (`consent_required=False`, `router.py:906`) with empty `consent_text`, and the frontend has no privacy UI (`grep privacy|consent|dpdp frontend/` → none). `data_retention_days` defaults `0` = keep-forever, and the retention reaper is **memory-backend-only** (`session_reaper.py:56-63,99-125`) — under Railway's Postgres it never runs, so student names + decisions + interview text persist on the volume indefinitely; `admin_audit.jsonl` and `facilitator_registry.json` also persist unrotated.
- **Why it matters (DPDP + institutional):** §5 expects a notice at collection; §8(7) expects storage limitation. 50 paying execs currently hand over names + a full decision trail with no disclosure.
- **Fix / mitigation:** set `consent_required=true` + a one-line `consent_text` per cohort (backend already records `consent_given_at`); after class, purge with `DELETE /api/admin/players` (the endpoint exists — this is manual, not missing). Put a calendar reminder to purge within N days.
- **Falsification attempted:** confirmed delete + self-service `export-my-data` + super-admin GDPR export all exist, so this is disclosure/retention hygiene, not absent capability.

### F18 — Config drift: a silent fallback swaps the shipped carbon parameters for divergent code defaults (0.05 → 0.15, 3×)
**P2 · CONFIRMED (live) · D6**

- **Evidence:** runtime reads only `simulation_config.json`; on any parse error it keeps `{}` and prints a warning (`config.py:111-116`), after which every constant reverts to its code default. Verified live: `simulation_config.json` has `carbon_price_growth_rate=0.05`, `carbon_price_base=50`; code defaults are `0.15` and `40.0` (`config.py:130-131`) — a 3× swing on growth. No schema validation; a missing key silently takes the divergent default. The Excel→JSON pipeline (`config_excel.py`) is offline and unvalidated, so editing the xlsx without re-import leaves runtime on stale values.
- **Failure scenario:** the config file is corrupted/truncated on a deploy the morning of class; the app boots fine, prints one unseen warning, and runs the graded cohort with carbon-price growth tripled.
- **Fix:** fail hard (refuse to start) if `simulation_config.json` is missing/unparseable or missing required keys; log the resolved value of each constant at boot; reconcile the code defaults to the shipped config.
- **Cheaper pre-class mitigation:** in the dry run, confirm the boot log shows the expected carbon parameters; don't hand-edit the xlsx without re-running the import.
- **Falsification attempted:** confirmed the JSON currently loads cleanly (so drift is latent, not active) — but it activates on any load failure or missing key, exactly the pre-session risk window.

### F19 — Non-durable volume boots green; a redeploy silently wipes the facilitator registry
**P2 (→P1 if volume misconfigured) · CONFIRMED · D1/D5**

- **Evidence:** `main.py:297-315` prints "RAILWAY DETECTED WITHOUT A DURABLE DATA DIRECTORY" but does **not** `sys.exit` (contrast the hard-fails at `:82`/`:156`); `/api/health` returns 200 with only `durable_storage:false` in the body (verified live: `durable:true` on my correctly-mounted probe, but the code path returns 200 either way).
- **Failure scenario:** `MURESSONS_DATA_DIR` unset or mounted at the wrong path → `facilitator_registry.json`, `token_versions.json`, `admin_audit.jsonl` live on ephemeral FS; app boots green; any redeploy wipes the registry → all facilitator accounts vanish mid-day and the emergency fallback activates.
- **Fix:** hard-fail boot (or return 503 from `/api/health`) when `on_railway and not durable`.
- **Cheaper pre-class mitigation:** before class, open `/api/health` and confirm `"durable_storage": true`; if false, fix the volume mount before students join.
- **Falsification attempted:** confirmed the only reaction to a non-durable volume is a `print`, and that the atomic-write + `.bak` + quarantine machinery is otherwise sound (so this is specifically a *silent-misconfig* risk, not a corruption risk).

### F20 — Client-side spend cap (shared CSF pool) is enforced nowhere — client or server
**P2 (fairness/integrity) · CONFIRMED · D8/D6**

- **Evidence:** the UI shows the CSF pool as one shared fund and warns "Over-allocated by X" (`ExecutiveCockpit.js:2435`), but the commit button is not `disabled` (`:4037`) and `preflightCommit` (`page.js:1307-1343`) doesn't block it. The backend recomputes `investment_ratio = clamp(capex/csf_pool, 0, 1)` **per BU** with **no sum-vs-pool check** (`router.py:2358-2375`); `grep` of the commit handler + `validation_logic.py` for a total/budget check → none.
- **Failure scenario:** a student (via the red button, or devtools/curl) allocates the full pool to every BU → each lands at ratio 1.0 (max investment everywhere), beating students who respect the cap.
- **Fix:** add a server check in `commit_turn` — reject when `sum(capex_allocated) > csf_pool` (400).
- **Cheaper pre-class mitigation:** none reliable (this is server-side) — best shipped as the one-line sum check; otherwise brief the room that the tool won't stop over-allocation and spot-check results.
- **Falsification attempted:** grepped the full commit path and pre-tick for any sum/total/exceed guard — only the per-BU clamp and a `capex ≥ $1` floor exist.

---

## 6. Verified-good (things that could have been wrong and are not)

- **Git history is clean of real secrets.** `git log --all -- <path>` = 0 commits for `.env`, `backend/.env`, `db/jwt_secret.key`, `backend/muressons.db`, `_to_delete/src*.tgz`, `sessions.json`, `master_password.json`. The only DB ever added (`backend/db/muressons_state.db`) was committed 0-byte. `_to_delete/` is not referenced by any `COPY`, so it never enters the image.
- **JWT is not forgeable and is stable for two-day resumption.** `JWT_SECRET` env wins; else the mounted-volume `/data/jwt_secret.key` (not the committed one, which is dockerignored + absent from history); else a persisted `token_hex(32)`. `main.py:147` `sys.exit(1)` if unset in prod.
- **Commit double-submit is well defended.** Per-session `asyncio.Lock` (409 on concurrent same-session), cross-process `pg_try_advisory_lock`, `uq_session_round UNIQUE(session_id, round_number)`, an `expected_round` optimistic check, and an R10 finale guard. Two-tabs and wifi-retry-with-fresh-client do not double-apply. (The one residual gap: a stale cached bundle that omits `expected_round` — set `REQUIRE_EXPECTED_ROUND=true` to close it.)
- **Round-advance vs in-flight commit race is handled** — force-advance defers to any in-flight real commit (`router.py:336-345`); a student who loses the race is auto-committed from their saved draft (degraded, not lost).
- **RBAC string-equality trap: clear.** No privilege *grant* uses `role == "super_admin"`; admin gates go through `is_admin_role()`/level comparison, so god_mode is included. Core live-run routes (pacing, unlock, player mgmt, shockwave, grading) correctly use `require_sim_manager` (excludes project_admin). The prior `caller_role == "super_admin"` bug is fixed.
- **Player tenancy is otherwise fail-closed** — `_assert_player_owns_session` guards every path-`session_id` player mutation except `set_username` (unauthenticated; worth a guard, but only mutates a display name/metadata).
- **Students cannot forge a facilitator JWT** — admin auth is the signed cookie only (the `X-Facilitator-Id` header fallback was removed); WebSockets authenticate inside the handler.
- **Dependency CVEs: none reachable.** `pip-audit -r backend/requirements.txt` → no known vulnerabilities; the team already replaced `python-jose` and bumped `python-multipart`/`python-dotenv`/`starlette`.
- **Third-party PII egress is inert by default.** `LLM_API_KEY`, `ELEVENLABS_API_KEY`, `SMTP_*`, per-cohort `webhook_url` all unset in every shipped env template; each module no-ops when empty. The webhook envelope carries IDs only. No student IP is persisted with identity (the `source_ip` audit line is facilitator-only).
- **RNG is seeded correctly where it's used** — per-cohort SHA-256 seed, independent `(seed, round, event)` streams; the core `process_tick`, black-swan and matrix-shock paths are deterministic. (The defect in F-sim is confined to the auxiliary engines that bypass this — see Coverage.)
- **Recovery affordances exist** for the runbook: Force-Advance, Undo-Round (multi-round, cohort-wide), pacing unlock/relock, player + facilitator password reset, Impersonate, God-mode Freeze/Unfreeze (commit path honours it with an actionable 503), and a backend-agnostic **Session Health** board.

---

## 7. Coverage and gaps

**Swept exhaustively:** the full route inventory (167 admin + player routes) for auth guards, including a complete unauthenticated-route enumeration (appendix in the D3 working notes); the RBAC ladder and every `require_*` guard; the commit/idempotency path end-to-end; the rate-limiter scoping; secrets in git history and `.dockerignore`/`Dockerfile` COPY reachability; paradigm × round config parity for all 5 paradigms × 10 rounds; env-gating of every third-party integration.

**Sampled, not swept:**
- The **216 KB `engine.py` / 147 KB `round_logic.py`** were navigated by grep, not read whole. Division-by-zero guards were spot-checked (several present), not proven exhaustive. **Untested path worth a targeted check:** the ~12 auxiliary scored engines (`impact_engine.py:92`, `org_politics.py:177`, `board_governance.py:251`, `supply_chain_network.py:486`, `regulatory_sandbox.py:875`) draw from the **unseeded global `random`**, so at round 5 identical decisions can yield a $12M climate-damage difference by luck and a session is not reproducible for a grading dispute. The sim worker demonstrated 2 distinct treasury outcomes across 8 identical-input runs. I did not fold this into the top-20 as its own ID only for space — **treat it as a P1 fairness finding**: route those draws through the seeded `event_rng` (remediation #15), or as an interim, `random.seed(event_seed(...))` at the top of `run_new_engines` and the r5 handler. This is the single most important item in this section.
- **CEO-interview GET routes** (`router.py:5813` questions, `:6011` results) take `session_id` from the path with no ownership assertion; not read end-to-end. 5-minute confirm before class: do they return another cohort's assessment content?
- **`admin_audit.jsonl` unbounded growth** and **`token_versions.json` non-atomic write** are real but P3 (slow-burn / rare); noted, not ranked.

**Could not test here (exact procedure for you):**
1. **Which branch/commit Railway actually deploys** — I cannot see the dashboard. Run: `curl https://<host>/api/health` and compare `build.commit` to `git rev-parse main`; check the Railway service "Source" branch.
2. **Real 50-user concurrency** — no cloud/Postgres-at-scale here. Run `load_tests/` (or a k6/locust script) against a **staging** Railway service with a throwaway DB: 3 cohorts × ~17 players, all committing within 60 s; watch for 503 "connection pool exhausted" and confirm whether commits are per-player or per-team (settles F09).
3. **Live redeploy on an open tab** — deploy to staging while a tab sits on the decision screen, then open the R2 materiality modal; confirm it recovers rather than looping (F16).
4. **Device/browser matrix + a11y on the commit path** — load the signed-in cockpit at 1280 px and on a 390×844 phone; confirm no horizontal scroll and that Commit is reachable (F on mobile); run the manual a11y checklist on the Commit button. The automated a11y suite never signs in, so the commit surface is currently un-gated for contrast/keyboard.
5. **Docker image contents** — `docker daemon` was unavailable here, so I verified image hygiene by reading `.dockerignore` + `Dockerfile` COPY lines rather than building. Build the image once and `docker run ... ls /app/backend` to confirm no `.env`/`muressons.db` shipped (the one stray is `backend/muressons.db`, not `.dockerignore`d — P3, add it).

---

## 8. Live-session runbook (print this page)

**Pre-flight (T-30 min), non-developer:**
1. Open `https://<host>/api/health` → confirm `"status":"ok"`, `"database":"postgres"` (not "memory"/"demo_mode":true), `"durable_storage":true`, `"low_disk_space":false`. If any is wrong, **stop and fix before students join.**
2. Confirm Railway auto-deploy is **off** for today. Do not push anything.
3. Log in as each facilitator/co-facilitator and **change the password**; delete unused facilitator accounts.
4. Confirm cohort settings: real paradigm (not `un_sdg`), `redact_peer_identities=true`, `consent_required=true` with a one-line notice.
5. Open the **Session Health** board and keep it open all session.

**The three most likely failures, their symptom, and the fix:**

| # | Symptom (what you'll see) | Most likely cause | Recovery action (you can do this) |
|---|---|---|---|
| 1 | Students report "internal server error" / "save failed" clustered at a round boundary; many at once | DB pool exhausted during the commit burst (F09) | Advance cohorts **one at a time**, not simultaneously. If it persists, restart the Railway service (the healthcheck won't do it for you — F04). Then Undo-Round the affected cohort one round and let them re-commit. |
| 2 | One student stuck on a round; screen said "everyone advanced" | Force-advance silently skipped them (F11) | On Session Health, find the student a round behind → **Impersonate** them → **Undo-Round** them one round → have them re-commit. Never assume Force-Advance took everyone; re-check the board after each advance. |
| 3 | A student's decisions "disappeared" after a reload, or a login is rejected | Draft lost in the 30 s autosave window (F12) / account password already changed by someone (F01/F08) | For lost draft: they re-enter and wait for the "saved" indicator before doing anything else. For rejected login: **reset their password** (facilitator or player reset endpoint) and watch the audit log for a login from an ID that shouldn't be active yet. |

**Facilitator overrides available (all in a couple of clicks):** Force-Advance, Undo-Round (cohort-wide, multi-round), pacing Unlock/Relock, player & facilitator password reset, Impersonate, and God-mode Freeze/Unfreeze (freezes all sims with a student-facing message — use it if you need to pause the room to sort something out).

**Escalation:** if `/api/health` is not reachable at all, or the whole room 429s on login (F10 — proxy-IP misconfig), that needs the developer / Railway dashboard; there is no facilitator-side recovery for those two. Everything else in the table you can handle from the admin console.
