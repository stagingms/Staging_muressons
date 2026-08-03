# Muressons — Phased Implementation Plan
**Companion to** `REVIEW_Muressons_Panel_2026-08-02.md` (item numbers `#n` refer to its remediation table)
**Written:** 2 August 2026 · **Author:** the three-voice review panel

## The two dates everything hangs on

| Date | Event | What must be true by then |
|---|---|---|
| **D+5** | Next live run — 10 people | Nothing can fail visibly in the room; no open security hole |
| **D+14** | **First graded run AND first 20-team cohort** (single cohort) | Results are reproducible; the run is reconstructable; 20 teams × 6 laptops does not fall over |

Everything else is elastic. These are not.

**One rule for the whole plan:** the golden traces (Phase 2) come before anything that touches the engine. Not because it is tidy — because without them you cannot tell a fix from a regression, and the whole point of D+14 is being able to tell.

---

## Phase 0 — Before the next run (D+1 to D+5) — ✅ **IMPLEMENTED 2026-08-02**

*Everything except the two items that are yours to do (0.2 rotate secrets, 0.11 rehearse the restore). Backend suite after: **1,876 passed, 2 failed** — both failures are artifacts of my sandbox not being a git checkout, not defects. Nothing here changes simulation behaviour; the golden traces do not exist yet, so no engine maths was touched.*

**New tests:** `backend/tests/test_phase0_run_day_fixes.py` (17), `test_join_password_not_bypassable.py` (5), `test_config_introspect.py` (14). **Updated:** `test_scale_preflight.py` — it asserted that Postgres alone unlocks multi-worker, which 0.12 deliberately changes; rewritten to pin both halves of the new contract rather than deleted.

| # | Task | Effort | Status |
|---|---|---|---|
| 0.1 | ✅ **Done.** Re-applied the `f3f5956` pacing fix — and found it worse than reported: commit **`42ac6b1` ("Accessibility: theme leaks…")** reverted it **on `main`**, not just in the working tree. `test_pacing_gated_modes.py` 7/7 green. Original `admin_router.py:3510,3514` — your working tree has `max(pacing["unlocked_round"], 1)` back, which against the default `999` is a no-op. **Manual and timed pacing currently gate nothing.** Go green on `tests/test_pacing_gated_modes.py` (6/6 red today) | 1 h | 🔴 **Do first** |
| 0.2 | ⬜ **YOURS** — rotate `JWT_SECRET`, `MASTER_PASSWORD`, `PROJECT_ADMIN_PASSWORD` | 15 min | ⬜ |
| 0.3 | ~~Finding 1 — `_bypass_password` query-param auth bypass~~ | — | ✅ **Done, applied, tested** |
| 0.4 | ✅ **Done.** `require_sim_manager` + `_assert_session_ownership`, and `player_id` removed from the payload (CohortPulse.js never read it). **#3** Guard `cohort-pulse` (`admin_router.py:11233` — no `Depends` at all; returns every team's `session_id` + `player_id`) | 30 min | 🔴 |
| 0.5 | ✅ **Done.** `frontend/app/api/health/route.js` moved to `_to_delete/`; the `/api/*` rewrite now reaches the backend. **#4** Health check — delete `frontend/app/api/health/route.js`. Verify after deploy: `/api/health` must return `"database":"postgresql"`, not `"service":"frontend"` | 20 min | 🔴 |
| 0.6 | ✅ **Done, with one deliberate deviation** — the client now sends it and treats a `stale_round` 409 as success-arriving-late; the server enforces it when present and logs when absent. **Not made mandatory yet**: a hard requirement would 422 any browser tab on a cached bundle, which is a run-day failure mode, and the double-advance originates in the client retry — so shipping the client half is what closes it. Flip `REQUIRE_EXPECTED_ROUND=true` once the warning stops appearing. **#5** from the client; make it required server-side (stops the retry double-advance) | 1 h | 🟠 |
| 0.7 | ✅ **Done** — plus **#17 early**: R10 decisions now reach the audit log (the branch was `for dec in decisions_raw: pass`). Needed a new parity-safe `log_decisions()` on both storage backends. **#6** Set `game_over` on the normal R10 path; reject commits when set (R10 is currently infinitely re-committable) | 1 h | 🟠 |
| 0.8 | ✅ **Done** — the poller now reports both transport failures and non-2xx responses. **#12** Set `connectionState` from the 5-second poller's catch block — one line turns the already-built `ConnectionBanner` from decorative into functional | 30 min | 🟠 |
| 0.9 | ✅ **Done** — `_fa_round`/`_fa_deadline_at`/`_fa_force` are now in `_PACING_LOCAL_FIELDS`, so the 3-second refresher can no longer revert a Force Advance. **#13** in `force_advance_cohort`; add `_fa_*` to `_PACING_LOCAL_FIELDS` | 30 min | 🟠 |
| 0.10 | ✅ **Done.** **§8.1 Phase A** — wire `deploy_preflight`; entrypoint tripwire for `scale_preflight`; disable the `market_dynamics` toggle; hide the `DryRunSimulator` tab (it 404s) | 2.5 h | 🟠 |
| 0.11 | ⬜ **YOURS** — **#20′** rehearse one restore onto a throwaway Railway service. Write down the steps and the elapsed time | 1 h | 🟠 |
| 0.12 | ✅ **Done.** `WEB_CONCURRENCY>1` now also requires `MURESSONS_MULTIWORKER_VERIFIED=true`, with a warning naming the ~12 stores that would split. Postgres alone no longer unlocks it. | 1 h | ✅ |

**Exit criterion:** full suite green except the two `test_deploy_image_hygiene` git-metadata cases; `/api/health` reports the backend; pacing tripwire green.

---

## Phase 1 — The instrument (D+2 to D+4, overlaps Phase 0) — ✅ **IMPLEMENTED 2026-08-02**

*You retune daily. This is the half of that loop that does not exist yet.*

| # | Task | Effort | Status |
|---|---|---|---|
| 1.1 | ~~**#47** `GET /api/admin/config/live` — what the process is *actually* running~~ | — | ✅ **Built, 14 tests, mounted** |
| — | **Note on my own error, recorded because it is the exact failure mode this plan warns about.** While adding `log_decisions` I wrote `database.py` and `database_memory.py` from a stale snapshot and silently reverted your committed **TEAM-3** work (`team_consensus` nullability — NULL meaning "not recorded" rather than a fabricated `'majority'`). I caught it on the post-commit diff review, restored both files from `HEAD`, and re-applied `log_decisions` on top with matching no-coercion semantics. Final diff vs HEAD: **73 insertions, 0 deletions.** Same shape as `42ac6b1`: a large write from a stale base, quietly undoing a same-day fix. **Always read `git diff --stat HEAD` before committing a regenerated file.** | — | ✅ Fixed |
| 1.2 | ✅ **Done.** `frontend/app/components/ConfigLiveStatus.js`, rendered directly under the uploader in `SimulationSwitchboard` (god-mode → Sim Switchboard). Verdict line first, then problems worst-first with their messages intact, then the fingerprint; all 238 constants behind a `<details>` with a name filter. Re-reads itself automatically after a successful upload — the one moment the answer matters most. Colours use `tokens.css` semantic tokens only. **9 tests** (`__tests__/config-live-status.test.js`), RTL against the real DOM rather than source regex, plus one narrow wiring check because this repo has shipped an orphaned component before. Mutation-verified: silently dropping the problems list fails 2 of them. | 3 h | ✅ |
| 1.2a | ✅ **Done.** Corrected the uploader's copy. It said *"Changes take effect immediately — no server restart required"*; both halves were false (the reload rebinds ~5 of ~13 consumer modules, and the file it writes lives in the image). It now says to verify below, and names the JSON-and-redeploy path as the one that sticks. A test asserts the old sentence never comes back. | 15 min | ✅ |
| 1.2b | ✅ **Done.** Updated the `sim_switchboard` sidebar tooltip to describe what the tab now renders (`CLAUDE.md` convention: change the tab, change the tooltip, same commit). | 5 min | ✅ |
| 1.3 | **Use it as a habit:** after every tuning change, call it. `problems: []` means the value you set is the value the engine is using. Anything else tells you exactly which of the three failure modes you hit | — | 🟠 |

**What it already detects, verified against your code:** an on-disk `simulation_config.json` the process never loaded; a partial hot-reload leaving consumer modules on old values (proven — a simulated reload of `SIM_ROUNDS` flags **four** stale modules); god-mode overrides that beat the constant; and 16 `_engine_tunables` keys with no downstream consumer at all.

> **Until Phase 3 lands, retune only by editing `simulation_config.json`, committing, and redeploying.** It is the one path that means what it says. The Excel importer writes into the image (reverted by the next redeploy) and hot-reloads only 5 of ~13 consumer modules; the god-mode sliders forward 2 of 24 values.

---

## Phase 2 — The safety net — ✅ **6 of 7 done, 2026-08-02**

*Done: 2.1, 2.2, 2.3, 2.4 (file delivered, see note), 2.5, 2.6. Remaining: **2.7 — confirm CI actually gates**, which is yours. Suite: **1,920 passed, 2 xfailed**, 2 pre-existing sandbox failures.*

| # | Task | Effort | Status |
|---|---|---|---|
| 2.1 | ✅ **Done.** `tests/test_financial_golden_trace.py` + `tests/golden/financial_trace.json`, 6 tests, deterministic. **Building it found that a faithful money oracle must replicate `post_tick` AND the router's reporting-truth resync** — without the resync the engine's mid-pipeline `historical_ebitda` persists and compounds to −26bn on a zero-capex run. Also: I claimed it covered the three unseeded engines, then instrumented and counted — a full run makes exactly **3** bare-`random` draws and those engines never fire. Claim corrected; the count is now a pinned invariant that fails in both directions. **#9 Financial golden trace.** Clone `test_stakeholder_golden_trace.py` onto the money surface: treasury, EBITDA, tCO₂e, synergy, per-BU revenue/opex/CI, plus final M_R and terminal valuation. Synthetic committed script (you have no recorded run — §9.6). Pin to `tests/golden/financial_trace.json`, same rebaseline ritual | 2 days | 🔴 **Highest value in the plan** |
| 2.2 | ✅ **Done, differently than planned.** I measured the waterfall before asserting it and **it does not hold** — unexplained treasury movement reaches **$656M** on a sim that opens with $50M. Asserting `residual == 0` would have swapped an invariant that cannot fail for one that always does. `tests/test_treasury_waterfall.py` therefore measures and reports it, with unconditional finiteness assertions that CAN fail. Chasing it found something larger: **`run_deterministic_simulation` was not deterministic** — it seeds the global `random` module, but engine paths draw from `event_rng`, which returns a system-seeded `Random()` when the cohort seed is absent, and the harness never set one. So every invariant in `test_universal_math_engine.py` has been evaluated against a different simulation each run. One-line fix applied; residual entropy recorded as strict xfail. **Lead**: `SINGLE_BU_PHARMA/legacy_abc`'s residual is exactly its `total_capex`. | 3 h | ✅ |
| 2.3 | ✅ **Done** in `tests/conftest.py`. **#32** Autouse fixture that snapshots/restores `random.getstate()`. 18 files seed the global RNG; none restore. Without this a green run is not evidence the next run is green | 1 h | 🔴 |
| 2.4 | ⚠️ **File delivered — you must apply it.** `.github/workflows/ci.yml` is protected against remote writes, so copy the delivered version over yours. It extends the `backend-postgres` job to run the goldens, the treasury waterfall, the full-run game, the route guards and the Phase 0/1 suites against **real Postgres**, not just `test_postgres_parity.py`. | 4 h | ⚠️ |
| 2.5 | ✅ **Done** as a **ratchet** — `tests/test_admin_route_guards.py`, 11 tests. Measured: of **286** admin routes, **69 had no role guard** and **68 session-scoped routes never checked ownership**. Fixing 137 gaps five days before a cohort would be reckless (a wrongly tightened guard locks a facilitator out mid-workshop), so the counts are ceilings that may only go down, with a slack check so progress gets banked. **Fixed outright**: `/{session_id}/debrief`, `/{session_id}/peer-evaluations`, `/{session_id}/bonuses`, `/annotations/{session_id}`, `/{session_id}/messages` — all served student PII or assessment data with no check of any kind. Ratchet mutation-verified. **#7** Two RBAC tripwires: every `@admin_router` route has a `Depends(require_*)`; every route with `{session_id}`/`{cohort_id}` calls `_assert_session_ownership`. Allowlist the deliberate exceptions | 3 h + fixes | 🟠 |
| 2.6 | ✅ **Done.** `tests/test_full_run_e2e.py` — 9 tests, a full R1→R10 game over HTTP in ~4s (cooldown popped, not slept). Every response asserted; values asserted at game over; the Phase 0 fixes (game_over guard, stale-round 409) verified end to end. **Found a pre-existing off-by-one**: `insert_next_round` logs decisions under the round the commit CREATED, so round 1 has no rows and every set is filed one round late — any debrief or grade reconstruction reads the wrong round. Recorded as strict xfail; fixing it is a two-backend migration, not a pre-run edit. | 1 day | ✅ |
| 2.7 | Confirm CI is actually gating (branch protection + Railway "Wait for CI"). **The 6 red pacing tests on your disk are the argument**: a tripwire nothing runs is not a control | 1 h | 🔴 |

**Exit criterion:** `pytest` twice in a row gives identical results; golden traces gate in CI on both backends.

**Do not start Phase 4 until this is green.** Stated explicitly so it is not inferred.

---

## Phase 3 — Make the configuration real (D+7 to D+10, or slip past D+14)

*Slippable — the JSON-and-redeploy path works. Do it as soon as the graded run is behind you.*

| # | Task | Effort | Behaviour risk |
|---|---|---|---|
| 3.1 | **#37** Route `simulation_config.json` and `decision_overrides.json` through `runtime_paths.data_dir()` (your `/data` volume is verified mounted and writable). Migrate the committed file in on first boot if absent | 3 h | None |
| 3.2 | **#38** Convert `from config import X` to `config.X` attribute access in the ~13 consumer modules; re-resolve `process_tick` through the module. Then one `importlib.reload(config)` is sufficient *and honest* | 1 day | ⚠️ Low — **run the golden trace before and after; any diff is a value that was silently inert** |
| 3.3 | **#39** `round_logic.py:2102` — fall back to `FINANCIAL_SHADOW_CARBON_PRICE` instead of the literal `250` | 1 h | ⚠️ Low |
| 3.4 | **#22** CSF pool: add both keys to `simulation_config.json` + `config_excel.py`, use the constants at `router.py:360`, serve the pool from the server and delete `page.js:392`'s copy | 4 h | ⚠️ Low |
| 3.5 | **#29** `_engine_tunables`: wire all 24 or delete it. `config/live` now names the 16 that reach nothing | 4 h | ⚠️ Low |
| 3.6 | **§8.1 Phase B** — `dry_run.py` as a working pre-flight. **Remove the global `random.seed()` at `:119` first** (it rewinds every live cohort's RNG), fix `hash(sid)` at `:230`, add the route, offload to a thread. **Gated on 4.3** | 1 day | ⚠️ Low after 4.3; **High before** |

---

## Phase 4 — Reproducibility (D+5 to D+10) — **hard deadline D+14**

*This is what makes a graded run defensible. Ordered by dependency.*

| # | Task | Effort | Behaviour risk |
|---|---|---|---|
| 4.1 | **#18 first.** BU-ordering parity: order both backends by the canonical `DEFAULT_SLOTS`; target the micro-strike by `bu_id` not index (`engine.py:2515`); drop the `int()` at `database_memory.py:802` | 3 h | ⚠️ Medium — changes which BU is struck. Production is Postgres and every test is memory-mode, so **today the strike lands differently in production than in any test you have run** |
| 4.2 | **#14** Auto-generate a per-cohort seed at creation; display it; allow override. Reproducibility must not be an unticked checkbox | 2 h | ⚠️ Medium |
| 4.3 | **#15** Convert the 12 bare-`random` engine sites to `event_rng`. All are live (§9.10). Then delete the three `*_enabled: False` lines from the stakeholder golden and let it cover them | 1 day | ⚠️ **High — do only after Phase 2.** Rebaseline once, review the diff deliberately |
| 4.4 | **#16** CEO interview: no `random.uniform` fallback (return data scores + `llm_used: false` and a visible banner), pin the model to a dated snapshot, `temperature=0`, cache by `(session_id, hash(responses))`. **Back to High — it is graded at D+14** | 4 h | ⚠️ Low |
| 4.5 | **#17** R10 audit rows — `router.py:2606` is `for dec in decisions_raw: pass`. The graded finale currently has no decision record | 1 h | None |
| 4.6 | **#19** `_audit()` on the six graded-outcome actions: `apply_override`, `undo_round`, `force_advance_cohort`, `set_pacing`, `unlock/relock`, `delete_session` | 3 h | None |
| 4.7 | **#27** Stamp the config fingerprint (from `config/live`) + the seed onto `sessions.metadata` at creation | 4 h | None |
| 4.8 | **#43** Persist the full commit envelope (`dividends_paid`, `pillar_decisions`, `emergency_credit_used`, `engagement_action`, `force_override_cfo`, `investment_ratio`) into `decision_audit_log.metadata`, so the D+14 run becomes a real replay fixture | 4 h | None |

**Exit criterion:** `replay(session_id)` reproduces the stored terminal state, asserted in CI on a committed fixture run.

---

## Phase 5 — Capacity for 20 teams (D+9 to D+12) — **hard deadline D+14**

| # | Task | Effort |
|---|---|---|
| 5.1 | **#46** Per-cohort cache for the commit-progress scan. ~120 pollers × ~23 queries every 5 s ≈ **550 q/s** for one badge; all six observers per team run the identical 20-sibling scan. A 2–3 s TTL cache is ~an 80× reduction for ~30 lines. **Cheapest capacity win available** | 4 h |
| 5.2 | **#33a** Make decision-regret opt-in. It runs `process_tick` **two extra times per commit** — 20 commits become ~60 serial ticks. Straight 3× CPU reduction | 2 h |
| 5.3 | **#33b** `run_in_executor` for `process_tick` — see the Scaling Track for what this does and does not buy | 4 h |
| 5.4 | **#33c** Send `?since_range=`/`?since_round=` from the client so every poll stops re-serialising the full 10-round history | 2 h |
| 5.5 | **#44 interim** Gate the read-path auto-commit trigger to *driver* callers. Today an observer's poll can force-commit another team's round, and with 5 observer laptops per team that is likely rather than possible | 1 h |
| 5.6 | **Rehearse the load.** `load_tests/throughput_test.js` at 20 teams × 6 observers, against a staging deploy. Rehearse on D+12, not on D+14 | 4 h |

> `MAX_PLAYERS_CEILING = 20`, and that module's own docstring says a larger cohort *"has never been exercised by the round engine's peer-comparison or leaderboard paths."* **Your first graded run sits exactly on the untested edge.** 5.6 is not optional.

---

## Phase 6 — Structure (post-D+14, with the second engineer)

| # | Task |
|---|---|
| 6.1 | **Step 3 — extract `sim/`.** Move `engine`, `round_logic`, `balance_sheet`, `terminal_valuation` and the config tables into a package with no imports from `router`/`admin_shared`/`database`. `process_tick` takes `ScenarioConfig` and `Seed` explicitly (Phase 4.7 already put both on the run). **The golden traces must not move by a digit** — that is how you know the move was clean |
| 6.2 | **Step 4 — `RunService` + a real state machine.** One module owns locking, idempotency, the transaction boundary, the audit write and publication. Absorbs #24, #25, #28, #44-proper |
| 6.3 | **Step 5 — split the routers.** Back on the roadmap now a second engineer is coming. Catalogs to data modules first, then `config_admin`, `excel_admin`, `settings_admin`, `god_mode_admin`. **Only after 2.5** — the guard tripwires are what make it mechanical rather than a game of spot-the-missing-`Depends` |
| 6.4 | **#41/#42** Cross-tenant: scope the freeze per cohort, scope `broadcast_students`, replace `ALTER TABLE … DISABLE TRIGGER` with `SET session_replication_role = replica`. **Only when you actually run two cohorts at once** |
| 6.5 | **§8.1 Phase C** — decide on `market_dynamics`. It changes replay from per-team to per-cohort; gated on 6.2 |
| 6.6 | **#30** Delete the six frontend/backend rule divergences (M_R copy, case catalog, glossaries). Serve from the API |

### Second engineer, week one
`#7` (guard tripwires) → `#35` + `#45` (dead code, dormant toggle). Isolated, zero behaviour risk, and it forces a read of the import graph, `CLAUDE.md` and the tripwire suite — the fastest honest tour of this system. **No rule changes until Phase 2 is green.** Write down one thing before they arrive: `terminal_valuation.py:175` is the authoritative M_R, and the comment twelve lines into the authoritative R10 function states the wrong coefficient and the wrong maximum.

---

## The Scaling Track — recommended way forward on `WEB_CONCURRENCY`

**Short answer: stay on one worker, deliberately, and make one worker fast enough. Do not add workers to solve a load problem — for your workload it would not help much and it would break about fifteen things.**

### Why more workers is the wrong first move

Two workers means two *separate copies* of every module-level dict, and they never talk. What breaks immediately: the `MUR-NNN` and `FAC-NNN` counters (duplicate ids), the cohort-quota check, `decision_overrides.json` (concurrent clobber), rate limits (N× more permissive), and every facilitator note, bonus, peer evaluation and annotation (visible only on the worker that served the request). `scale_preflight.py` clamps to 1 when Postgres is absent — **you are on Postgres, so it will happily honour `WEB_CONCURRENCY=4`.** The clamp protects the memory backend, not the shared-state assumption.

Also worth separating two things that sound alike: **multiple concurrent cohorts ≠ multiple workers.** One worker serves many cohorts fine. Your cross-tenant issues (#41/#42) are about *global mutable state*, not about process count.

### Step 1 — make one worker sufficient (Phase 5, before D+14)

This is almost certainly the whole answer for 20 teams.

- **Reads:** #46 removes ~98% of query volume. 120 pollers × 20 sibling queries → one scan per cohort per 2–3 s.
- **Writes:** #33a (decision-regret opt-in) removes two thirds of tick CPU immediately.
- **Responsiveness:** #33b (`run_in_executor`) — **be precise about what this buys.** `process_tick` is CPU-bound pure Python, so a thread pool does **not** parallelise it; the GIL still serialises the work. What it buys is that the event loop stays free, so the other 119 clients keep getting dashboard responses while a tick runs instead of queueing behind it. That is exactly the failure you would see at 20 simultaneous commits — so it is the right fix — but do not expect throughput to multiply.

Measure before deciding anything further. `main.py:446-466` already logs per-request latency correlated by session id; the p95 on `/commit-turn` and `/dashboard` during the D+12 load rehearsal is the number that tells you whether Step 2 is needed.

### Step 2 — if ticks become the wall: a process pool, not more workers

`process_tick` takes dicts and returns dicts. That makes it a near-perfect fit for `ProcessPoolExecutor`, which gives **real** parallelism (separate interpreters, no GIL) **without touching the shared-state assumption at all** — the engine has no shared state to split; only the orchestration around it does.

This is the cheapest genuine scaling step available to you, and it is another reason Phase 6.1 (extract `sim/` as a pure package) pays for itself: a pure engine is one you can hand to another process. Rough shape: 2–4 workers in the pool, tick payload pickled in, result pickled out, the round still persisted by the single web process.

### Step 3 — real multi-worker, only if you ever need it

Only after externalising the ~15 per-process stores catalogued in §2.5 of the review. The good news: **#28 already does most of that work for durability reasons** (facilitator notes, bonuses, peer evaluations and annotations must move to the store anyway, because today a restart erases a day of assessment data). Multi-worker then becomes largely a side effect. What remains after #28: the two id counters (derive from `max(existing)+1` or a DB sequence), the cohort quota (a DB check), and rate limits (DB or Redis).

Gate the switch on evidence, not intent — and you already have the harness: `load_tests/split_brain_probe.js` flips a freeze on one worker and asserts every other worker converges. Do not raise `WEB_CONCURRENCY` until that probe is green against a real two-worker deployment.

### Now: a guardrail (#48, Phase 0.12, ~1 hour)

Because the clamp does not protect you where you actually are:

1. In `scale_preflight.safe_worker_count`, refuse `WEB_CONCURRENCY > 1` unless `MURESSONS_MULTIWORKER_VERIFIED=true` is also set, with an error naming what breaks. Currently the *only* condition it checks is "is Postgres active" — which is true, so the gate is open.
2. At boot, when workers > 1, log the inventory of per-process stores that are about to be split. The information should exist at the moment it is cheap to act on — the same principle `deploy_preflight.py` was written on.
3. A tripwire test asserting the refusal, so the guard cannot be removed casually.

---

## What is deliberately not in this plan

- **A rewrite.** The engine is nearly pure, the case table is readable, the immutability spine is right, and the test infrastructure is better than most teams manage. Everything wrong here is reachable incrementally.
- **`Decimal` for money.** Deterministic IEEE-754 on a pinned CPython replays fine; 400+ `round()` sites is a large diff for a benefit the conservation assertion (2.2) gives you more cheaply.
- **Redis / a message queue.** At one worker and 20 teams, `coordination_store` over Postgres `LISTEN/NOTIFY` is adequate. Adding infrastructure adds a run-day failure mode you cannot debug in the room.
- **TypeScript on the frontend.** The typing problem that costs you is in `round_logic.py` (78% untyped), not in React.
- **Alembic.** Single writer, additive schema. **But add the tripwire pinning `db/init.sql` equal to the auto-schema in `database.py:92-240`** — they are currently kept in sync by a code comment, in a repo that has tripwires for the role ladder and the shockwave catalog.
- **Rewriting the 23 regex-over-source frontend tests.** Freeze them, stop writing new ones, let them decay.

---

## If you slip

Slip **Phase 3** (config plumbing — keep using JSON-and-redeploy) and **Phase 5.3/5.4**, and if you are still short, **cap the first graded cohort at 10 teams.**

**Never slip Phase 2 or Phase 4.** A slower run you can explain beats a faster one you cannot — and the one asset you cannot buy back later is the ability to say, three months from now, exactly why a student got the number they got.
