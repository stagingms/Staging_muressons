# Muressons Simulation — Architecture, Security & UX Audit

**Date:** 2026-07-15  **Auditor:** Senior architecture / security / UX review
**Scope:** Full local codebase (`backend/` FastAPI + `frontend/` Next.js), pre-GitHub, deploys to Railway on push.

---

## Stack (confirmed from code — no clarifying questions needed)

- **Backend:** FastAPI (Python 3.12), single `uvicorn` process bound to `127.0.0.1:8000`, fronted by Next.js. Entry point `backend/main.py`.
- **Frontend:** Next.js 15 (App Router), served by `next start` on Railway's `$PORT`. `next.config.mjs` proxies `/api/*` → backend. Both run in **one container** via `docker-start.sh`.
- **State store:** Dual backend selected at boot (`main.py:36-170`). `database_memory.py` (in-process dicts + JSON snapshot to `db/muressons_state.db`) OR `database.py` (PostgreSQL via asyncpg). Postgres path *mirrors* rows into `database_memory._sessions` as a synchronous cache.
- **Real-time:** WebSockets (`admin_router.py:6802,6832`) for God-Mode pushes + broadcasts, with REST **polling fallback** (`page.js` intervals at 8s/15s). Player WS is receive-only.
- **Auth:** Signed JWT (HS256) in `HttpOnly; Secure; SameSite=Strict` cookie for facilitators/admins; players use `X-Player-Id` + session-ownership. Role ladder in `admin_shared.py:ROLE_HIERARCHY`.

**Overall:** This codebase has been through many prior security passes (SEC-1…6, HIGH-0xx, MED-0xx, C-1…6 tags throughout). The auth core, RBAC, destructive-action guards, and commit concurrency are notably mature. The remaining risk is concentrated in **deployment-model durability** (Railway restarts), a handful of **committed default credentials** and **input-validation gaps** — and, decisively, a **scale mismatch**: the current single-worker, in-memory-coordination design is built for one classroom (~5–40 users) but is targeted at **~500 concurrent users (~100 cohorts)**. That scale gap (§1.2) is now the single largest piece of work and gates the durability spine (§1.1/§1.3) behind it.

---

# 1. Core structure & architecture

### 1.1 Ephemeral live-run state is lost on every Railway restart/redeploy — **CRITICAL (structural)**
- **Evidence:** Live operational state lives in module-level dicts, not in the `db` abstraction:
  - `admin_shared.py:203` `_god_mode_settings` (includes `system_frozen`), `admin_shared.py:761` `_round_pacing` (which rounds are unlocked, timers), `router.py:119` `_session_players`, `router.py:122` `_commit_timestamps`, `router.py:128` `_commit_locks`, `admin_router.py:39` `_rate_buckets`.
  - Railway deploys **on push** and restarts the container; `railway.json` also sets `restartPolicyType: ON_FAILURE`.
- **What happens on restart mid-session:** Even in **PostgreSQL mode** (where sessions/scores *are* durable), `_round_pacing` resets to empty → `is_round_unlocked()` falls back to defaults, so a live cohort's carefully-paced unlock state is lost and teams can desync or stall. `system_frozen` clears (a paused room silently un-pauses). Free-advance timers and cohort commit barriers reset. In **in-memory mode** (the committed `.env` default), *everything* — sessions, decisions, scores — is gone. `_session_players` has a rebuild path (`router.py:600-614`); `_round_pacing` does **not**.
- **At 500-user scale this stops being just a restart risk:** once you run more than one worker/replica (which 500 users forces — §1.2), the same in-memory dicts are *also* split across processes at steady state, not only lost on restart. So the fix below is a prerequisite for scaling, not merely for durability.
- **Fix:** (a) Persist pacing/freeze/pacing-timer state to a **shared** durable store (Postgres table, or Redis for the hot coordination keys) — not a per-process JSON snapshot — and rehydrate in the `lifespan` startup hook alongside the existing cohort-seeding loop (`main.py:197-224`). (b) Document that a push = a restart, and gate deploys during live sessions. (c) Railway's zero-downtime/health-check window won't help — the process identity changes, so in-memory state is always dropped. **Effort: L.**

### 1.2 Single-container, single-process architecture cannot serve 500 concurrent users — **CRITICAL (scale)**
> **Scale target (confirmed by owner): ~500 concurrent users.** At 5 players/cohort that is ~100 live cohorts running simultaneously. This finding is re-rated from HIGH to **CRITICAL** and is now the gating architectural constraint — the whole in-memory state model (§1.1, §1.3) breaks the moment you add the second worker/instance that 500 users require.
- **Evidence:** `docker-start.sh` runs backend + frontend in one container; backend bound to `127.0.0.1:8000`, started with `uvicorn main:app` and **no `--workers` flag** (single worker = one CPU core of Python, one event loop). Railway runs one such container. The commit mutual-exclusion path even documents that Postgres advisory locks matter *only* when multi-worker (`router.py:1363-1377`) — i.e. single-worker is the current assumption.
- **Why 500 users breaks this — two compounding walls:**
  1. **Throughput wall.** One uvicorn worker serves every request on one event loop; `process_tick` (the engine) is synchronous CPU work. 100 cohorts polling `/dashboard` every 8–15s (§6.1) plus commit bursts at round boundaries will saturate a single core long before 500 users. There is no `--workers`, no replicas, and one crash-loop takes down all 500 users at once (the bash restart loop recovers the process but drops all in-memory state per 1.1).
  2. **Shared-state wall (the harder one).** The fix for the throughput wall is "add workers/replicas," but **every piece of live coordination state is a per-process Python dict**, so multiplying processes silently corrupts it:
     - `_commit_locks` / advisory lock (`router.py:128`, `1348-1377`): the `asyncio.Lock` is per-process. Cross-process safety exists **only** via the Postgres advisory lock — so multi-worker is safe *only if* running on PostgreSQL and that path is exercised. On memory mode it's a no-op → two workers double-commit the same team.
     - `_rate_buckets` (`admin_router.py:39`): per-process → N workers = N×10 effective login attempts, weakening the brute-force guard proportionally to replica count.
     - `_round_pacing`, `_god_mode_settings` (`admin_shared.py:761,203`), `_session_players`, `_commit_timestamps` (`router.py:119,122`): each worker holds its own copy, so a facilitator's unlock/freeze/pace action lands on **one** worker and players pinned to other workers never see it. The room desyncs by design.
- **Impact:** As written, the system is a single-classroom (~5–40 user) tool. Pointing 500 users at it will not "just be slow" — it will give wrong pacing, split-brain freeze state, and double-commits. This is a **re-architecture prerequisite, not a tuning task.**
- **Fix (ordered, and a hard dependency for the 500-user launch):**
  1. **Mandate PostgreSQL** for the scaled deployment (memory mode is disqualified — SEC-2 already hard-fails it in prod; keep it that way). **Effort: S** (config/ops).
  2. **Move all shared coordination state out of process memory** into Postgres and/or Redis: rate-limit buckets, `_round_pacing`, `_god_mode_settings`/freeze, commit timestamps, and the cohort-commit barrier. This subsumes §1.1 (durability) and depends on §1.3 (stop reaching around `db`). **Effort: L.**
  3. **Run multiple uvicorn workers + horizontal replicas** behind Railway's load balancer only *after* (1)+(2); verify the Postgres advisory-lock commit path is actually taken under load. **Effort: M.**
  4. **Split frontend and backend into separate services** so the Next.js tier scales independently of the Python tier (today they share one container/lifecycle). **Effort: M.**
  5. **Load-test at 100 cohorts / 500 users** before go-live (see §6.1 for the exact scenario). **Effort: M.**
- **Interim (if 500 users must run before the re-architecture):** shard cohorts across multiple independent single-worker instances with sticky routing so each cohort's players always hit the same process (keeps the per-process dicts coherent), and cap users/instance. This is a stopgap, not the target design. **Effort: M.**

### 1.3 Business logic reaches around the `db` abstraction into `database_memory` — **HIGH (coupling / Postgres durability)**
- **Evidence:** 28 direct references to `database_memory` internals from route handlers: `router.py` (18) and `admin_router.py` (10) — e.g. `router.py:1011` `import database_memory as _dm; sess = _dm._sessions.get(session_id); … _dm._persist()`; also `router.py:2710, 3717, 3918, 4019…`. Solo-start (`router.py:1011-1068`) writes `is_solo`, `pacing_mode`, `_solo_round_configs` **only** to `_dm._sessions` + `_dm._persist()`.
- **Impact:** In Postgres mode these writes hit the in-memory *cache* and the JSON snapshot, never the database → they are **not durable** and are lost on restart (see 1.1). It also hard-couples game logic to one storage implementation, so "swap the store" is not actually possible and any new store must reproduce `database_memory`'s private dict shapes.
- **Fix:** Route all session mutations through the `db` interface (add `db.update_session_fields(...)`, `db.set_solo_config(...)`), and have both `database.py` and `database_memory.py` implement them. Remove direct `_dm._sessions[...] = …` writes from handlers. **Effort: L** (mechanical but wide surface).

### 1.4 Adding a new round type / role is moderately painful — **MEDIUM**
- **Evidence:** Round config is dispatched by `if paradigm == …` chains (`router.py:1030-1045` solo seeding, and again in `_commit_turn_impl`), and paradigm-specific config lives across `round_configs.py`, `pillar_configs.py`, `sdg_configs.py`, `healthcare_configs.py`. Roles are pinned by drift tripwires across three files (good), but a new role means editing `ROLE_HIERARCHY`, `sidebarConfig.js`, `ROLE_ALLOWED_TABS`, `assignable_roles_for`, plus the sync test.
- **Impact:** New paradigms require touching several branch points; easy to miss one (the codebase already carries fallbacks like `get_pillar_config(rnum) or get_round_config(rnum)`).
- **Fix:** Introduce a paradigm registry (`PARADIGMS = {"un_sdg": SdgProvider(), …}`) with a common `get_round_config(rnum)` interface, replacing the `if/elif` chains. Roles: keep the tripwire, but document the "change-all-N-files" checklist in `CLAUDE.md` (partially there already). **Effort: M.**

### 1.5 Business rules duplicated across dashboards — **MEDIUM** (see §4 for specifics)
- Calculations are server-authoritative (good — §2.7), but display-side formatting/derivations exist in `frontend/app/utils/` (`formatCurrency.js`, `roundToQuarter.js`, `mrJourney.js`) and are re-implemented per component. Consistency is enforced by convention, not a shared module import everywhere.

---

# 2. Security vulnerabilities (must-fix list)

### 2.1 Committed default god-mode / project-admin passwords — **CRITICAL**
- **Evidence:** `backend/config.py:34` `MASTER_PASSWORD = _mp if _mp else "sim2026@iim"` and `config.py:50` `PROJECT_ADMIN_PASSWORD = … else "simadmin2026@"`. `config.py` **is tracked in git** (`git ls-files` confirms). `MASTER_PASSWORD` is the god-mode break-glass that "overrides every player/facilitator login" (`main.py:147-156`).
- **Impact:** Anyone with repo read access (or who finds the public GitHub repo) knows the live god-mode password. If the operator does **not** set `MASTER_PASSWORD` in Railway env, production boots with `sim2026@iim` armed. The boot only prints a *warning* (`main.py:147`), it does not refuse. The local `.env` (untracked, gitignored) also literally contains `MASTER_PASSWORD=sim2026@iim`.
- **Fix:** Remove the hardcoded fallbacks — default to empty (bypass **disabled**) and require an explicit env var to arm break-glass, mirroring how `PLAYER_MASTER_PASSWORD` already defaults to disabled (`config.py:43`). Rotate `sim2026@iim` / `simadmin2026@` immediately since they are in git history. **Effort: S.**

### 2.2 Well-known default player/facilitator password — **HIGH**
- **Evidence:** `admin_router.py:319` `plaintext = "Muressons123"` for every new player and facilitator (`admin_router.py:1577,1806,1916,2364`).
- **Impact:** Predictable initial credential. Mitigated by `must_change_password=True` on every creation, so it's only exploitable in the window before first login — but in a classroom an attacker who knows a peer's player-id could log in first.
- **Fix:** Generate a random per-user temp password (as `_generate_emergency_password` already does for `FAC-EMERGENCY`), shown once to the facilitator. Keep `must_change_password`. **Effort: S.**

### 2.3 `decisions` list is unbounded — **MEDIUM**
- **Evidence:** `models.py:261` `decisions: list[BUDecision]` with no `max_items`. `CommitTurnRequest` fields are otherwise well-bounded (`ge/le` on ratios, severities).
- **Impact:** A crafted commit can carry an arbitrarily large decisions array → memory/CPU amplification through `process_tick`. Low-skill DoS.
- **Fix:** `Field(..., max_items=<max BUs, e.g. 12>)`; reject unknown `bu_id`s server-side. **Effort: S.**

### 2.4 Player identity is a bearer UUID when `X-Player-Id` is omitted — **MEDIUM**
- **Evidence:** `router.py:137-157` `_assert_player_owns_session`: "The header is OPTIONAL for backward compatibility … clients that omit it fall back to UUID-as-bearer-token." If no header, ownership is **not** checked.
- **Impact:** Anyone who learns a session UUID (URL sharing, logs, screen-share) can drive that team's dashboard and commit turns, unless the client happens to send `X-Player-Id`. The check is opt-in from the attacker's perspective.
- **Fix:** Make `X-Player-Id` (or the player WS ticket / a player JWT) **mandatory** for all state-changing player routes; treat missing identity as 401. The WS side already did this hardening (`admin_router.py:6832` "raw session_id is no longer accepted as a bearer credential") — bring REST to parity. **Effort: M** (needs a coordinated frontend change to always send the header).

### 2.5 CORS auto-appends Railway domain but `allow_methods/headers=["*"]` with credentials — **LOW**
- **Evidence:** `main.py:264-270` `allow_origins=_cors_origins` (good, explicit list), but `allow_methods=["*"], allow_headers=["*"], allow_credentials=True`.
- **Impact:** Origin allowlist is the real control and is correct; wildcard methods/headers only widen what allowed origins may send. Low risk given SameSite=Strict cookies, but tighten for defense-in-depth.
- **Fix:** Enumerate the methods/headers actually used. **Effort: S.**

### 2.6 Emergency-fallback logs plaintext credentials — **LOW**
- **Evidence:** `admin_shared.py:672-687` logs the default facilitator id/password/role in a banner when the registry file is missing ("SENSITIVE: do not forward to public log collectors").
- **Impact:** Railway captures stdout/stderr; the plaintext could land in log aggregation. Self-documented as a known trade-off (it's the recovery path).
- **Fix:** Log an instruction ("restore db/facilitator_registry.json") without the plaintext; surface the credential only on an authenticated admin endpoint. **Effort: S.**

### 2.7 Positive findings (verified, no action needed)
- **Server-authoritative calculations:** `router.py:1596-1608` recomputes `investment_ratio = clamp(capex/csf_pool,0,1)` server-side, ignoring the client-supplied ratio (closes VULN-002). Engine `process_tick` runs server-side only.
- **No secrets in client bundle:** grep of `frontend/app/config`, `lib` finds no passwords/keys; auth persisted to `localStorage` is booleans/ids only (`roleRouting.js:roleAuthSubset`, "no PII").
- **`.env` not tracked** (gitignored + `.dockerignore:9`), so it is not baked into the image.
- **RBAC is level-based** (`is_admin_role`, `require_sim_manager` vs `require_facilitator`), header-injection auth removed (`get_fac_role` SECURITY-CRIT-002), token-version kill-switch (`auth_jwt.create_facilitator_token` `ver` claim), rate limiting on all login/role-change/pw paths (`admin_router.py:115`) with trusted-proxy allowlist and restart-surviving bans.
- **Injection:** No raw SQL string interpolation seen; asyncpg parameterized. No `eval`/`exec` on user input.

---

# 3. Robustness (failure paths)

### 3.1 Player disconnect & rejoin mid-round — **OK, minor gap**
- **Current:** Session id cached in `localStorage`; `page.js:328` `resumeSession(cachedId)` retries on load and **keeps the id even on failure** (NEW-07). WS reconnects with 5s backoff (`page.js:817`), REST polling continues regardless.
- **Correct:** As implemented. **Gap:** in-flight (uncommitted) decisions are only saved via `saveDecisions` autosave; verify unsaved slider state survives a refresh. **Fix / test:** *requires runtime testing* — load a round, change allocations, hard-refresh before committing, confirm values restore. **Effort: S** to add an explicit local draft cache if the test fails.

### 3.2 Facilitator refresh during a phase transition — **MEDIUM**
- **Current:** Pacing/unlock state is in `_round_pacing` (in-memory). A facilitator refresh re-reads it fine *within a process*, but if the refresh coincides with a **redeploy** the pacing state is gone (see 1.1). WS admin channel reconnects.
- **Correct:** Pacing must be durable and reloaded. **Fix:** as 1.1. **Effort: L** (shared with 1.1).

### 3.3 Two users submit conflicting actions in the same instant — **OK (well handled)**
- **Current:** Three layers: per-session `asyncio.Lock` with deterministic 409 fast-fail (`router.py:1348-1362`), Postgres advisory lock for cross-process (`router.py:1371-1377`), and optimistic `expected_round` guard returning 409 "Stale round" (`router.py:1456-1466`). Per-session 5s commit cooldown (`router.py:1401-1409`).
- **Correct:** As implemented. Verify the advisory lock is a true no-op sentinel in memory mode and doesn't deadlock. *Requires runtime testing* with two simultaneous commits. **Effort: none unless test fails.**

### 3.4 Malformed / out-of-sequence requests — **OK, one gap**
- **Current:** Pydantic validates types/ranges; `expected_round` rejects out-of-sequence; round > 10 → 409; locked round → 403. **Gap:** unbounded `decisions` (2.3) and unknown `bu_id` not rejected.
- **Fix:** bound + validate bu_id membership (2.3). **Effort: S.**

### 3.5 Session left idle past timeout — **MEDIUM**
- **Current:** JWT expires (default 2h, `JWT_EXPIRY_HOURS`; docs say set 8 for full-day). Player sessions have `end_date` lockout (`router.py:1432-1445`) and solo sessions "expire in 24h" (comment) — but no server process actually purges idle in-memory sessions; `_commit_locks`/`_commit_timestamps`/`_session_players` grow unbounded for the process lifetime.
- **Correct:** Idle sessions should be reaped and their locks GC'd. **Fix:** periodic sweep in the lifespan loop removing sessions past `end_date`/solo-expiry and their lock/timestamp entries. **Effort: M.**

### 3.6 Silent error swallowing on the player client — **MEDIUM (robustness+UX)**
- **Evidence:** `page.js` has 18 `catch(() => {})` / empty catches (paradigm poll, side-track poll, broadcast, force-override). Commit failure does surface (`page.js:746` plays error sound + logs), but many background fetch failures are invisible.
- **Impact:** A player whose poll silently fails sees a stale board with no indication; a facilitator change (paradigm/side-track) may never arrive.
- **Fix:** Route background-fetch failures to a lightweight "reconnecting / out of date" banner rather than swallowing. **Effort: M.**

---

# 4. Internal consistency

### 4.1 Drift tripwires exist and are the right pattern — **positive**
- **Evidence:** `backend/tests/test_role_hierarchy_sync.py` (role ladder ↔ `sidebarConfig.js`), `frontend/__tests__/shockwave-catalog.test.js` (catalog ↔ `_SHOCKWAVE_EVENTS`), `test_p6_master_secret_separation.py`. `CLAUDE.md` documents "change one, change the other, same commit."
- **Action:** *Requires runtime testing* — run `pytest backend/tests/test_role_hierarchy_sync.py` and `npm test -- shockwave-catalog` to confirm they currently pass (the working tree has uncommitted `MM` changes to `admin_shared.py`, `admin_router.py`, `models.py`, and **deleted** tests `test_archetype_solvency_gate.py`, so drift is plausible right now). **Effort: S to run.**

### 4.2 Corrupt git index + accidentally-staged deletions — **HIGH (process/consistency) — RESOLVED during this engagement**
- **Original evidence:** `git status` appeared to show `MM` (staged + further unstaged) on `router.py`, `admin_router.py`, `admin_shared.py`, `database_memory.py`, `models.py`, `round_logic.py`, plus five files staged as **deleted** (`test_archetype_solvency_gate.py`, `ESGWeightsEditor.js`, `StakeholderAvatar.jsx/.module.css`, `UX_V3_PHASE_NOTES.md`). Deploy-on-push means whatever is committed ships.
- **Root cause (found during Fix #8):** the `.git/index` was **corrupt** (`bad signature 0x00000000` — a zeroed index), left behind with a stale `.git/index.lock` from an interrupted `git commit` on 2026-07-13. The apparent `MM` "code drift" was a **phantom of the corrupt index** — every backend/frontend source file is in fact byte-identical to HEAD. The five staged "deletions" were real staging artifacts but the files were never removed from disk (all identical to HEAD) and all still imported/used (`ESGWeightsEditor` in both admin pages, `StakeholderAvatar` in `StakeholderAgentPanel`, the solvency-gate test covers live `round_logic` functions).
- **Resolution applied:** rebuilt the index from HEAD (`rm .git/index && git reset`, working tree untouched). Post-repair the tree is coherent — no phantom drift, the five files are tracked/clean, and no staged deletions remain. Full suite re-run: **1083 passed, 6 failed (all the shared login-rate-limiter test-isolation artifact, each passing in isolation)**. Drift tripwires green: role-hierarchy sync (2/2) and shockwave-catalog lockstep (4 events).
- **Residual (owner's call, not a defect):** genuinely uncommitted content remains — 19 regenerated `docs/*.docx/.pptx/.md`, three untracked `REVIEW_*` planning docs, and an untracked new component `BoardroomDebate.js/.module.css` that is **not imported anywhere** (WIP or dead code — wire it in or discard before committing).
- **Fix / follow-up:** commit the coherent tree; treat the corrupt-index episode as a signal to avoid interrupting `git commit` and to add a lightweight pre-push CI gate (`pytest -q` + `npm test`) so a corrupt/partial index or a red suite can't reach Railway. **Effort: S (reconcile — done) + S (CI gate).**

### 4.3 Server ↔ dashboard state cannot drift for scores — **positive, with a caveat**
- Scores/state come from `GET /{id}/dashboard` computed server-side; the client renders, doesn't recompute. **Caveat:** solo/`is_solo` and pacing flags written only to memory (1.3) *can* drift between what Postgres holds and what the dashboard shows after a restart. Fixed by 1.3.

### 4.4 Terminology / number formatting is convention-enforced, not import-enforced — **LOW**
- `formatCurrency.js` exists but each component formats independently; there is no single metric-label constant map. Risk of the "same KPI, two labels" class of bug the `CLAUDE.md` slotting rule is trying to prevent.
- **Fix:** Centralize KPI labels + formatters in one module imported everywhere. **Effort: M.**

---

# 5. UI / UX per dashboard

### 5.1 Player dashboard — next action & feedback — **MEDIUM**
- **Positive:** Countdown timer, decision-pressure timer, demo-mode banner, sound feedback on commit/error. Resume-on-reload is robust.
- **Issues:** (a) Silent background-fetch failures (3.6) undercut "feedback after every action is immediate and unambiguous." (b) With multiple independent 8s/15s polls plus WS, a mid-round facilitator change can appear up to 8–15s late with no "updating…" cue. (c) `page.js` is 1,915 lines — the "next required action" logic is spread across many effects; verify the primary CTA is always the single most prominent element per the one-slot rule in `CLAUDE.md`. *Requires runtime testing / screenshot review.*
- **Fix:** Add a connection/staleness indicator; consolidate polling into one coordinator; screenshot-audit the CTA prominence at 1280/1440/1920 widths. **Effort: M.**

### 5.2 Facilitator dashboard — see-all + two-click intervene — **MEDIUM**
- **Evidence:** `admin/facilitator/page.js` (2,247 lines), `war-map` (cohort ops + situation map), `trading-floor`, `CohortPulse.js`, teleprompter. The "X of Y teams committed" badge (`router.py:_cohort_commit_progress`) gives at-a-glance progress.
- **Issue:** Cannot confirm "all teams' status at a glance" and "intervene in ≤2 clicks" without runtime review — the surface is large and split across tabs (dashboard_home, timeline, war-map, trading-floor). *Requires runtime testing:* open a live cohort, count clicks from landing → inject shockwave to one team.
- **Fix:** If >2 clicks, add a per-team quick-action row on `dashboard_home`. **Effort: M** (pending test).

### 5.3 Admin (God Mode) — destructive-action guards — **STRONG (positive)**
- **Evidence:** `god-mode/page.js:1017` typed phrase `DELETE ALL DATA` + countdown for `reset-all`; `:1107` typed `DELETE` for hard-deleting live cohorts; orphan purge behind confirm modal. This is best-practice and exceeds the bar in the brief.
- **Minor:** Confirmations use a mix of `ConfirmModal` and native patterns; standardize on the modal. **Effort: S.**

### 5.4 Responsive behavior — **MEDIUM / requires runtime testing**
- **Evidence:** `CLAUDE.md` slotting rule notes the projector/atmosphere layer turns "off <1280px" and dims under `data-allocation-open` — so responsiveness is designed. But participants "on laptops of varying sizes" need the **core decision flow** usable down to ~1280 and ideally 1024.
- **Test:** Load the player board at 1280, 1366, 1440; confirm KPI belt + canvas stage + commit CTA are all reachable without horizontal scroll. **Effort: S to test, M to fix if broken.**

### 5.5 Loading / error states — **MEDIUM**
- **Evidence:** `page.js` uses `.catch(() => {})` widely (3.6); `next.config.mjs` sets `devIndicators: false` (suppresses dev overlay). No global error boundary observed for the player tree.
- **Fix:** Add a React error boundary + explicit loading skeletons + a global "server unreachable" state. **Effort: M.**

---

# 6. Anything else material

### 6.1 Load at 500 concurrent users — **CRITICAL / requires load testing** (see §1.2)
- **The number:** 500 users ≈ 100 cohorts. Each player runs a WebSocket plus polls on 8s and 15s intervals (`page.js`), and the facilitator dashboards poll on top. Back-of-envelope steady-state: ~500 dashboard reads / 8s ≈ **60+ req/s of `/dashboard` alone**, all on **one** uvicorn worker that *also* executes the synchronous `process_tick` engine on every commit. Round-boundary commit bursts (up to 100 cohorts committing within a facilitator-advance window) stack on top. One core will not hold this.
- **This is the runtime face of §1.2** — it is not independently fixable by "tuning." The polling reductions below help, but the core requirement is multiple workers/replicas on shared state (§1.2 fix steps 1–4).
- **Load test to run before go-live:** ramp `GET /dashboard` + `POST /commit-turn` to **100 cohorts × 5 players = 500 virtual users** (k6/Locust), with all 100 cohorts committing inside the same 5s advance window. Measure: p95 `/dashboard` latency, `/commit-turn` p95, the 5s-cooldown / advisory-lock 409 rate, worker CPU saturation, and — critically — whether pacing/freeze actions from a facilitator propagate to **all** players when >1 worker is running (the split-brain check from §1.2). Target: p95 < 1s, zero pacing desync.
- **Fixes:** (a) the §1.2 scale re-architecture (multi-worker + shared state) — prerequisite. (b) Coalesce the two client polls into one coordinator and lean on WS-push instead of polling; use the existing `since_round` param (`router.py:1286`) to trim payloads (§5.1/#10). (c) Consider read-caching `/dashboard` per (session, round) since it's immutable once a round is committed. **Effort: L** (dominated by §1.2).

### 6.2 Observability for live debugging — **MEDIUM**
- **Evidence:** Logging is mostly `print(...)` to stdout (startup, persistence, free-advance, solo-start). Generic 500 handler hides tracebacks in prod (`main.py:297-306`, good) but there's no request-id / structured logging to correlate a facilitator's "team X is stuck" with server events. Audit trail exists (`db/admin_audit.jsonl`) for admin actions only.
- **Fix:** Adopt structured logging (JSON) with session_id/request_id; keep the admin audit log. **Effort: M.**

### 6.3 Accessibility — **MEDIUM / requires runtime testing**
- Non-technical executives under time pressure benefit most from a11y. No evidence reviewed of color-contrast tokens beyond `tokens.css`, focus management, or keyboard operability of the commit flow. `CLAUDE.md` mandates semantic color tokens (good foundation).
- **Test:** Run the `design:accessibility-review` pass / axe on the player board; check contrast of danger/success KPI deltas and keyboard reachability of the commit CTA. **Effort: M.**

### 6.4 Maintainability — **MEDIUM**
- `admin_router.py` is **10,117 lines**; `router.py` 5,854; `page.js` 1,915. These god-files concentrate risk and make review/merge hard (the `MM`/deleted-test working tree in 4.2 is a symptom). ARCH-002 already extracted teleprompter/resources/analytics sub-routers — continue that decomposition.
- **Fix:** Split `admin_router.py` by domain (pacing, registry, interventions, sessions); extract player-board effects from `page.js` into hooks. **Effort: L.**

---

# Consolidated remediation plan (sequenced by severity + dependency)

Ordering rule: security break-glass first (cheap, no dependency, immediate blast-radius), then the **scale/durability spine** — which for a 500-user target is one connected epic (§1.2 + §1.1 + §1.3 + §3.2/§3.5/§4.3 + §6.1): you cannot add the workers 500 users need until shared state is out of process memory, and you cannot move shared state until handlers stop reaching around the `db` layer. Then input-validation, robustness/UX, and maintainability. No later item undoes an earlier one.

**Two tracks run in parallel:** Track A (security/correctness quick wins, items 1–4, 9) can ship immediately by small changes and is independent of scale. Track B (items 5–8) is the scale epic and is the **long pole** — it must complete before any real 500-user event.

| # | Fix | Area | Sev | Effort | Depends on |
|---|-----|------|-----|--------|-----------|
| 1 | Remove committed default `MASTER_PASSWORD`/`PROJECT_ADMIN_PASSWORD` (default to disabled); **rotate** `sim2026@iim` & `simadmin2026@` (already in git history) | 2.1 | **Critical** | S | — |
| 2 | Reconcile working tree; restore the 5 accidentally-deleted files; run full suite; confirm drift tripwires green before next push | 4.2, 4.1 | High | S | *(analysis done; blocked only on host `.git/index.lock`)* |
| 3 | Randomize per-user temp passwords instead of `Muressons123` | 2.2 | High | S | — |
| 4 | Bound `decisions` list + validate `bu_id`; enumerate CORS methods/headers | 2.3, 2.5, 3.4 | Med/Low | S | — |
| 5 | **Externalize ALL shared coordination state** to Postgres/Redis: rate-limit buckets, `_round_pacing`, `_god_mode_settings`/freeze, commit timestamps/locks, cohort-commit barrier, `_session_players` — with `lifespan` rehydrate. (Subsumes the old "persist live-run state" item.) | 1.1, 1.2, 3.2 | **Critical** | L | 6 |
| 6 | Route all session mutations through the `db` interface; remove direct `_dm._sessions[...]` writes (prerequisite for #5; also fixes solo-start durability) | 1.3, 4.3 | High | L | — |
| 7 | **Scale out:** mandate PostgreSQL; run multiple uvicorn workers + Railway replicas; verify the advisory-lock commit path under load; split frontend/backend into separate services | 1.2 | **Critical** | L | 5, 6 |
| 8 | **Load-test at 100 cohorts / 500 users** (k6/Locust); verify p95 latency and zero pacing/freeze split-brain across workers | 6.1, 1.2 | **Critical** | M | 7 |
| 9 | Make `X-Player-Id` (or player token) mandatory on state-changing player routes | 2.4 | Med | M | client sends header (§5.1) |
| 10 | Idle-session reaper + lock/timestamp GC (once state is shared, do it in the store) | 3.5 | Med | M | 5 |
| 11 | Stop swallowing background-fetch errors; add connection/staleness banner + React error boundary + loading skeletons | 3.6, 5.1, 5.5 | Med | M | — |
| 12 | Consolidate player polling into one coordinator; lean on WS-push; use `since_round`; cache immutable `/dashboard` per (session,round) | 6.1, 5.1 | Med | M | 11 |
| 13 | Runtime UX passes: facilitator ≤2-click intervene, responsive 1280–1440, a11y/axe, draft-survives-refresh, two-commit race, drift tests | 3.1,3.3,5.2,5.4,6.3 | Med | M | app running |
| 14 | Centralize KPI labels/formatters; standardize on `ConfirmModal` | 4.4, 5.3 | Low | M | — |
| 15 | Paradigm registry to replace `if/elif` config dispatch | 1.4 | Med | M | — |
| 16 | Structured logging w/ session/request ids (also essential to debug a 500-user live room) | 6.2 | Med | M | — |
| 17 | Decompose `admin_router.py` / `router.py` / `page.js` god-files | 6.4, 1.2 | Med | L | 16 |
| 18 | Remove plaintext credential from emergency log banner | 2.6 | Low | S | 1 |

**Do first, today:** #1 and #2 (both S, no dependencies, highest immediate risk; #2's analysis is already complete — see the Fix-#8 work — and only needs the host git lock cleared).

**The gating epic for the 500-user launch:** #6 → #5 → #7 → #8, in that order (each is a hard prerequisite for the next). Treat this as the critical path; it is L-heavy and should start now, because nothing about a 500-user event is safe until #8 passes. Track A security items (#1, #3, #4, #9) and observability (#16) can proceed alongside it. Everything from #11 down is post-scale hardening.

---

### Items explicitly marked "requires runtime testing"
3.1 (draft survives refresh), 3.3 (two-commit race / advisory-lock no-op), 4.1 (drift tests currently pass), 5.1/5.2/5.4 (CTA prominence, ≤2-click intervene, responsive), 6.1 (load), 6.3 (a11y). Exact tests are described inline in each finding.
