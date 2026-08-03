# Muressons — Three-Voice Architecture & Code Review
**Date:** 2 August 2026 · **Reviewed at:** `main` @ `eeddd71` (366 commits, 2026-03-17 → 2026-08-02)
**Panel:** Principal Architect (**PA**) · Staff Engineer (**SE**) · Simulation-Modelling & Pedagogy (**SMP**)

**Evidence discipline.** Every claim is tagged **[F]** *fact — read it in the code, or reproduced it*, **[I]** *inference — strongly implied but not executed*, or **[A]** *assumption — could not determine*. File:line citations are against the tree as it stands on your disk today.

---

> **Revision 2 — 2 August 2026.** Updated after your answers to §10 and after verifying production configuration directly. Nine of the eleven open unknowns are now closed; one new dimension (**L — configuration and the calibration loop**) was added because your answer to "how often do you retune?" turned a cluster of Medium findings into the thing most likely to be wasting your time. The remediation table gained seven items and was re-ranked; the in-memory-backend call in "Deliberately not doing" was **reversed**. Changed sections: housekeeping, §1, §2.8, §3, §4.A, §4.D, new §4.L, §5, §6.0 and the tables, §8 (new Step 1.5), §9, §10.
>
> **Revision 7 — same day.** **Finding 1 is fixed and applied to your working tree**, with a 5-test regression file; your full suite was run before and after with identical results (see Housekeeping 2). Running it also surfaced **a live pacing regression on your disk** — `tests/test_pacing_gated_modes.py` 6/6 red, manual and timed pacing gating nothing (Housekeeping 3, now Finding 0). Your two new dates — **graded 20-team single cohort in 2 weeks** — and **yes to a second engineer** produced **§6.05 and §6.1: a dated 14-day plan**, moved #16 back to High, took #41/#42 off the critical path, and put Step 5 back on the roadmap.
>
> **Revision 6 — same day.** Confirmed 6 per team = 1 driver + 5 observers, each on their own laptop; the §4.D figures were already sized on that and are unchanged. Added two notes that came out of checking the seat model: the five observers share **one** credential, so the observer seat is a viewing mechanism and not an identity one (§9.9) — and, more urgently, **`router.py:767` is the one legitimate caller of `_bypass_password`**, so Exemplar 1's fix must make the parameter keyword-only rather than delete it, or every observer seat breaks. Added a regression test for that to Exemplar 1.
>
> **Revision 5 — same day.** Answered §10.4 and §10.5, and rewrote §10.3 in plain language after you said the `railway variables` line didn't make sense. Two findings came out of your answers: **#46**, a per-cohort cache for the commit-progress scan (observers on their own laptops ⇒ ~120 pollers ⇒ ~550 queries/second for one badge; the cache is an ~80× reduction for ~30 lines — the cheapest capacity win in this document), and **#47**, a `config/live` endpoint, because you use all three tuning paths and they silently overwrite each other. **Interim advice until Step 1.5 lands: retune only by editing `simulation_config.json` and redeploying — it is the one path that works.**
>
> **Revision 4 — same day.** Added **§8.1 — a phased plan for the four unreachable modules** (`scale_preflight`, `market_dynamics`, `dry_run`, `deploy_preflight`), at your request. They turn out to be four different problems in three different phases: two are an hour each and belong in Do-Now; `dry_run` is a genuinely valuable calibration instrument you are not using **but which would rewind every live cohort's RNG if wired as-is**; and `market_dynamics` is a modelling decision rather than a wiring task, because it changes replay from per-team to per-cohort. Remediation #34 was rewritten to point at §8.1, and Steps 0 and 1.5 of the migration path were updated.
>
> **Revision 3 — same day.** Two corrections you asked for, both of which changed the analysis. (a) **Scale**: 20 teams means 20 *committing drivers*, not 120 concurrent players. The write-path arithmetic was already sized on 20 and stands; the read-path figure is unchanged by the correction because poll load follows device count, not edit rights — the two are now costed separately in §4.D, and §10.5 asks the question that settles it. Checking this surfaced a defect I had missed: **the round barrier is enforced on the read path, so an observer's browser can force-commit another team's round** (new item #44, new drill row). (b) **Dormant engines**: you were right to ask me to name them — I hadn't. I built the import graph from `main.py` and traced all 97 backend modules; the full result is in §9.10. Headline: 91 of 97 are live, so your "all the engines are run" is essentially correct — but **`market_dynamics.py` (307 LOC) is genuinely dormant and has a live facilitator toggle that silently does nothing.**

## ⚠️ Read this first — housekeeping

1. **Rotate your production secrets.** To review this repo I copied `backend/` wholesale into an ephemeral Anthropic cloud sandbox. That included `backend/.env` and `backend/.env.railway`, which contain a live `JWT_SECRET`, `MASTER_PASSWORD` and `PROJECT_ADMIN_PASSWORD`. The sandbox is discarded when this session ends, and those files are correctly gitignored and dockerignored — but a secret that has left the machine it was minted on should be treated as spent. Rotate all three. **[F]** Verified: `.gitignore:15,18-19`, `.dockerignore:13-15`; `git log --all` shows `backend/.env*` and `.env` were **never** committed. Your secret hygiene is *good* — this is my footprint, not your bug.

2. ~~**There is a live, unauthenticated account-takeover bug.**~~ **✅ FIXED AND APPLIED TO YOUR WORKING TREE.** `backend/router.py` now has `_join_session_impl` (no route, keyword-only `bypass_password`) with `join_session` as a thin wrapper. The one legitimate caller — `player_login` at `router.py:770`, for observer seats after the view code is verified — is preserved. `backend/tests/test_join_password_not_bypassable.py` was added: **5 tests, all fail on the old code, all pass on the new.** I then ran your full backend suite before and after: **identical results (12 pre-existing failures in both, 1830 → 1835 passed)**, so the change introduces no regressions. Details in §7 Exemplar 1. **Still rotate the secrets (item 1) — that is separate.**

3. **🔴 NEW — a live pacing regression in your uncommitted working tree, found while running your suite.** `backend/tests/test_pacing_gated_modes.py` fails **6 of 6** against the code on your disk. Cause: your working tree reintroduces `pacing["unlocked_round"] = max(pacing["unlocked_round"], 1)` at `admin_router.py:3510` and `:3514` — which, against the default `unlocked_round = 999`, is a **no-op**. That is exactly the bug commit `f3f5956` ("Manual and Scheduled pacing actually gate rounds now") fixed today: `git show HEAD:backend/admin_router.py` has it only as a *past-tense comment* at line 3492, and the working tree has the code back. **[F]** Verified both ways. The uncommitted TEAM-1 observer-seats work (+547 lines across `router.py` and `admin_router.py`) appears to have clobbered it — a regeneration or merge artifact, not a deliberate revert.

   **Why this matters in five days:** manual and timed pacing are the facilitator's primary control, and right now, on the code on your disk, **setting either one gates nothing** — every round stays open. Your own tripwire caught it; it is red and nothing is watching. Re-apply the `f3f5956` change to those two branches and re-run `pytest tests/test_pacing_gated_modes.py` before you push. *(This is also the sharpest possible argument for §10.3's CI question: a green tripwire that nobody runs is not a control.)*

3. **Production configuration verified live** (2026-08-02, `https://cso.mastersustainability.org`). **[F]** `GET /health` returns `{"database":"postgresql","demo_mode":false,"durable_storage":true,"storage":{"data_dir":"/data","configured":true,"writable":true,"on_railway":true,"durable":true}}`. That is the *good* configuration on both axes — real Postgres, mounted durable volume. `GET /docs` is 404, so the API explorer is correctly disabled. **And in the same request I confirmed the health-check defect: `GET /api/health` — the path `railway.json` monitors — returns `{"status":"ok","service":"frontend"}`.** That is the Next.js static route, not the backend. Railway is watching the frontend and cannot see a dead backend. This was inference when I wrote it; it is now measured against your live deployment.
   *(I deliberately did **not** probe `cohort-pulse`, the join endpoint or any other unauthenticated surface against production — exercising those against real student data is not mine to do. The two reads above are benign.)*

---

## 1. Blunt verdict

The foundation is not wrong in the way a rewrite-warranting foundation is wrong — but it is missing the one boundary this product's whole value depends on. **There is no simulation engine boundary.** `engine.process_tick` is very nearly a pure function, and then it is called from the middle of a 776-line HTTP handler (`backend/router.py:2033-2809`) that also owns rate limiting, freeze checks, pacing gates, quiz gates, input rewriting, pillar aggregation, seven post-hooks, persistence, webhooks, board-pressure side effects *applied after persistence*, and response assembly. Around it, simulation rules live in a declarative table (`round_configs.py`, `pillar_configs.py`) **plus** ~27 imperative modules, with at least one rule that is unreachable in normal play (`round_logic.py:1834`) and at least one config key that two different code paths apply differently. The state that flows through all of this is an untyped `dict` whose entire 555-key event bag is persisted verbatim into `active_event_flags` each round (`engine.py:4083`) and then re-served through a hand-maintained 38-field allowlist (`models.py:115-186`) that the file's own comments document as a recurring source of silent data loss.

The consequence, in the terms that matter to you: **a Muressons run is not reproducible today, and in the default configuration it is not reproducible even in principle.** The stochastic seed defaults to empty (`admin_shared.py:347`); twelve engine-path randomness sites bypass the seeding layer entirely; the two storage backends return business units in different orders and the engine indexes into that list positionally, so the same seed strikes a different BU on Postgres than in memory (`database.py:889` vs `database_memory.py:784`, consumed at `engine.py:2514-2516`); memory mode truncates emissions to `int` (`database_memory.py:802`); half the commit envelope is never persisted, so there is nothing to replay from; and **50% of the graded CEO-interview competency score falls back to `random.uniform(-1.0, 1.0)` when the LLM is unavailable** (`router.py:5775-5781`). SMP's position, stated plainly: *in its current state this product cannot be defended as a grading instrument, and a debrief that says "here is why you got this number" is not fully truthful.*

**And a finding that only became visible once you told me you retune the model every day, alone (§9.7).** Your calibration loop is partly fictional and entirely ephemeral. `_engine_tunables` is a super-admin UI exposing 24 "engine constants" of which **22 are write-only** and 3 already contradict `config.py` by a factor of two (`admin_router.py:10105-10173`). Editing the shadow carbon price changes CAROIC and *not* the $250/tonne terminal carbon tax students actually see (`round_logic.py:2102`). The CSF pool constants are absent from both `simulation_config.json` and `config_excel.py`, so they cannot be authored at all. The Excel hot-reload reports `{"reload":"complete"}` while `round_logic.py`, `router.py` and ~8 other modules keep their old `from config import X` bindings — **a mixed-config process**. And the uploaded `simulation_config.json` is written to the *image* filesystem, not to `/data` (`runtime_paths.py:24-26` excludes config files deliberately), **so every Railway redeploy silently discards your tuning and reverts to the committed file.** If you have been calibrating daily against that loop, some fraction of the parameter changes you believe you made never took effect, and the ones that did have been reverted repeatedly. This is now the #2 cluster in the plan, above most of the concurrency work.

That said — and the panel is unanimous here — **this is not a careless codebase.** The immutability triggers (`database.py:184-238`), the backend-parity AST tripwire (`tests/test_backend_parity_surface.py`), the conftest that tests its own isolation (`tests/test_suite_does_not_touch_real_state.py`), the golden-trace harness with an explicit rebaseline flag (`tests/test_stakeholder_golden_trace.py`), the structured request/session-correlated access log (`main.py:429-466`), the coordination store with documented eventual-consistency semantics, the SEC-2/SEC-6 boot fail-fasts, the snapshot rotate-and-quarantine recovery path, the k6 split-brain probe — these are the instincts of someone who has been burned and learned. The problem is not judgement. The problem is **breadth without depth, by one person, at speed**: 194k lines across 526 source files, 232 admin endpoints, 366 commits in 20 weeks, one author (`git shortlog`: 353 of 366 commits, one email). The documentation has drifted ahead of the code in several places where it matters. You do not need a rewrite. You need about six one-line fixes before your next run, then a characterization harness, then one boundary.

**PA dissents on tone:** *"missing one boundary" undersells it. `admin_router.py` at 12,492 lines with 232 endpoints and 55 banner-delimited responsibility sections is not a router, it is an unpartitioned application. Eighteen months from now the cost of change is dominated by that file, not by the engine.*
**SE dissents back:** *and splitting it before there are tests is how you turn a working product into a broken one. The catalogs come out first; the endpoints stay put until the golden masters exist.*

---

## 2. System map (Phase 0)

### 2.1 Architecture — the real layering

**[F]** Python 3.12 / FastAPI backend (108k LOC, 268 files) + Next.js 16 / React 19 frontend (86k LOC, 258 files), one Docker container running both, deployed to Railway. Datastore is **two parallel implementations behind one duck-typed interface**, chosen at import and injected via `sys.modules["database"] = db` (`main.py:171-186`): asyncpg/PostgreSQL (`database.py`, 1744 lines) or an in-process dict store with a JSON snapshot (`database_memory.py`, 1443 lines). Real-time is **WebSocket for a handful of push events + 5-second REST polling for everything that matters**.

The intended layering (engine → round logic → router → UI) is roughly visible. The actual layering is:

| Layer | Where it actually lives | Leaks |
|---|---|---|
| Simulation math | `engine.py` (4239), `balance_sheet.py`, `terminal_valuation.py` | reads `admin_shared._god_mode_settings` directly at `engine.py:2616-2621` — a mutable process global inside the tick |
| Round/pedagogy rules | `round_logic.py` (2934) + `round_configs.py`/`pillar_configs.py` + 27 satellite modules | `_post_r10_grand_finale` is **766 lines**; `admin_router.py:7227` picks the graded R2 BU with bare `random.choice` |
| Orchestration | `_commit_turn_impl`, `router.py:2033-2809` (**776 lines**) | *is* the orchestration layer, the gating layer, and half the persistence layer |
| Transport/HTTP | `router.py` (73 endpoints), `admin_router.py` (232 endpoints) | domain catalogs live here: `_scenario_presets` (172 lines), `SWIPE_FILE_PRESETS` (97), `_engine_tunables` (26), `_SHOCKWAVE_EVENTS` |
| Persistence | `database.py` / `database_memory.py` | 44 scattered `update_latest_global_state` call sites do fetch-mutate-write with no concurrency control |
| UI | `frontend/app` | reimplements the CSF pool (`page.js:389-400`), a 10-round case catalog (`SustainabilityBalancedScorecard.js:2027-2091`), the M_R reward function (`mrJourney.js`), and the R1/R2 mandatory gates (`page.js:1001`) |

**Confidence: high.**

### 2.2 Domain model — anemic

**[F]** `models.py` (326 lines, 19 classes) contains **only HTTP DTOs**. There is no `Round`, `Team`, `Decision`, `Cohort` or `Scenario` type with behaviour. The only domain types anywhere are three dataclasses in `engine.py` (`CIDeltaResult:181`, `PendingProjectDelta:2120`, `TickContext:2294`), and `TickContext` is explicitly a mutable bag shared across pipeline stages. Parameter-typing census: `round_logic.py` is **78%** `dict`/`Any`/unannotated; `terminal_valuation.py` 52%; `engine.py` 27%; `admin_router.py` 15%. The rules core is the least typed part of the system and the HTTP edge is the most — exactly inverted.

**[F]** `engine.py:4083` assigns `"active_event_flags": events` — the entire round's output dict, ~555 distinct keys across the codebase including internals like `_base_treasury_internal`, becomes the persisted flag store. `GlobalStateOut` (`models.py:115-186`) declares 38 of them; Pydantic silently drops the rest. `models.py:161-167` documents in a comment that a field added to the store must be hand-added here or a player's mid-round allocations are silently lost on refresh.

**Vocabulary.** Mostly good — `cohort`, `round`, `decision`, `crisis`, `debrief`, `facilitator` all read the way a facilitator speaks. Three real overloads: **`session`** means (a) a cohort shell, (b) one team's run, (c) the auth session; **`simulation_mode`** means three different things and `admin_shared.py:885` disambiguates by *sniffing the value*; **`paradigm`** appears as `decision_paradigm` and `climate_paradigm` with the overlapping value `advanced_climate`. And the domain's central noun is missing: **there is no `Team` type and no `teams` table.** A team is modelled as a string suffix — `VIEW_CODE_SUFFIX = "-VIEW"`, `driver_id_for_view_code("MUR-004-VIEW") -> "MUR-004"` (`router.py:222-227`).

**Confidence: high.**

### 2.3 The state machine

**[F] There is no state machine.** There is no `advance_round()`, no transition table, no status enum. A round advances *per team*, as a side effect of that team persisting round N+1. Cohort-level constructs are gates and barriers, not closers.

- **Round advance** is centralised: 3 `insert_next_round` call sites (`router.py:2610`, `router.py:6763`, `admin_router.py:3255`).
- **Everything else about state** is not: **44** `update_latest_global_state` call sites (22 in `router.py`, 22 in `admin_router.py`), each an unguarded fetch-mutate-write.
- **Pacing** is a process-local dict `_round_pacing` (`admin_shared.py:1406`) with **39 direct assignment sites** across 3 files; `unlocked_round` alone has 8.
- **Triggers that open/close a round:** player commit; `unlock_next_round` (`admin_router.py:3583`); timed single-shot task (`:3272`); multi-round schedule task (`:3339`); time-derived unlock (`admin_shared.py:1443` — restart-safe, good); the all-teams barrier in `free` mode (`router.py:434-458`); free-advance timeout (`router.py:490-508`); `force_advance_cohort` (`:3389`); practice-mode reset (`router.py:2665`); cohort end-date lockout (`router.py:2075`).
- **Reversible:** undo round (`admin_router.py:8968` → `database.py:1349`), relock round (`:3609`, floored at highest committed round — well designed), unfreeze, turnaround abort, practice reset. **Irreversible:** R10 in-place update, Extended Horizon.
- **[F] The barrier is enforced on the READ path.** `_cohort_advance_status` (`router.py:434`) is called from `get_dashboard`, and it is what performs the auto-commit side effect (`router.py:502-509`). **If nobody polls, Force Advance and the timeout never fire.** The 5-second client poll (`useSimulation.js:689`) is the de-facto scheduler.

**Confidence: high for the mechanics; medium for the exhaustiveness of the trigger list** (the surface is large enough that I would not swear there is no 11th trigger).

### 2.4 The round-resolution path (the crown jewel)

```
POST /api/simulations/{sid}/commit-turn                     router.py:1957
  └─ commit_turn (lock wrapper)                             router.py:1963
      ├─ _assert_player_owns_session  (SEC-3, before lock)  router.py:1972 / :228
      ├─ asyncio.Lock fast-fail → 409                       router.py:1979-1985
      ├─ pg_try_advisory_lock(hashtext(sid)) → 409          router.py:1996 / database.py:281
      └─ _commit_turn_impl  (776 lines)                     router.py:2033
          ├─ 13 sequential gates (rate limit, freeze, end-date, round>10,
          │  expected_round, pace lock, unlock, quiz gate, side-track,
          │  BU validation, pre_tick validation)            router.py:2044-2301
          ├─ deshuffle_choice (server rewrites client input) router.py:2210
          ├─ COR-1 recompute of investment_ratio            router.py:2288
          ├─ pre_tick                                        round_logic.py:125
          ├─ process_tick  ← THE ENGINE                      engine.py:4127
          │     _run_stochastic_layer → _run_financial_layer
          │     → _run_operational_layer → _run_reporting_layer
          │     → _assemble_global_state                     engine.py:4227-4239
          ├─ R10 clamp new_round = 10                        router.py:2346
          ├─ pillar aggregation, flag re-seed                router.py:2377-2459
          ├─ post_tick (mutates state in place)              round_logic.py:431
          ├─ run_new_engines  ← wrapped in one bare except   router.py:2481-2488
          ├─ reporting-truth resync                          router.py:2512-2522
          ├─ persist:  R1-9 insert_next_round (transactional)
          │            R10  update_latest_global_state       router.py:2599-2613
          ├─ …then MORE writes outside the transaction:
          │   auto-inject interventions, cohort commit count,
          │   CEO diary, decision-regret shadow ticks (2 extra
          │   process_tick calls!), board pressure             router.py:2630-2799
          └─ 201 + full state + events   ← ONLY the committing client sees this
```

**[F] No WebSocket push on commit.** `grep push_to_session router.py` → one hit, the practice-mode reset. Every other client learns of the advance on its next 5-second poll. **[F]** The pacing pushes that *do* exist are keyed to the **cohort** id while players subscribe with their **child** session id (`admin_router.py:3325/3360/3558/3591/3651` vs `router.py:1126`), so `round_unlocked` never reaches cohort players; and `game_advanced`, which `page.js:881` listens for, is emitted by no backend code at all.

**Confidence: high.**

### 2.5 Concurrency and real-time model

**[F]** Default deployment is **1 uvicorn worker, 1 replica** — `docker-start.sh:21-25` calls `scale_preflight.safe_worker_count`, which returns `WEB_CONCURRENCY` (default 1) and clamps to 1 unless Postgres is the backend. This is a deliberate, well-reasoned gate: `scale_preflight.py:4-9` states plainly that a second worker would split-brain the classroom, and `coordination_store.py:42-45` / `ws_fanout.py:28-31` both mark their multi-worker paths as not yet soak-tested. **The panel agrees this is the right call today.**

**[F]** Nine locks exist. **Exactly one is cross-process** (the Postgres advisory lock). `_cohort_lock`, `_fac_registry_lock`, `_config_file_lock`, `_save_lock` are all per-process and all claim in comments to prevent duplicates that they would not prevent at `WEB_CONCURRENCY>1`. **[F]** There are **no** `SELECT ... FOR UPDATE` statements and **no** optimistic version columns anywhere in the repo.

**[F]** Round resolution is **not** one transaction. `insert_next_round` is atomic (`database.py:1090-1167`); the ~50 awaits before it and the ~6 writes after it are not. Correctness rests entirely on the two locks, which means every path that mutates round state *without* taking them — notably `undo_latest_round` (`admin_router.py:9019`) — is unprotected.

**Confidence: high.**

### 2.6 Test reality

**[F]** 1,485 collected backend tests across 126 files in `backend/tests/`, plus 320 frontend jest tests across 34 files. CI **does** exist and is tracked on `main` (`.github/workflows/ci.yml`, 4 jobs: pytest memory-mode, **a real Postgres parity job**, jest, `next build`). *(Correction to my own first pass: an earlier sweep missed this because of how I staged the tree. `jest.setup.js`, `babel.config.js`, `eslint.config.mjs`, `package-lock.json` and `.gitignore`/`.dockerignore` all exist too.)* The Postgres parity job as a deploy gate is genuinely good design and rarer than it should be.

But what is *asserted*:

- **[F] One golden master exists** — `tests/test_stakeholder_golden_trace.py` + `golden/stakeholder_slo_trace.json`. It runs a real seeded 10-round pipeline and asserts byte-equality. It is the best test in the repo. **Its capture surface is reputation, social licence, governance risk and NPC satisfaction only.** Treasury, EBITDA, tCO2e, synergy, M_R and terminal valuation — the entire financial core, i.e. the part students are graded on — have **no** characterization test.
- **[F] It is only green because it turns the problem off.** `test_stakeholder_golden_trace.py:66-78` disables `org_politics`, `board_governance` and `supply_chain` with the comment that those *"roll on the bare global `random` module (un-seeded) and are the only entropy sources once the stochastic_seed is set."* All three default to **on** in production (`round_logic.py:681,706,725`).
- **[F] The one named conservation invariant is a tautology.** `test_universal_math_engine.py:483` asserts `treasury_end == next.treasury_start` — but `run_deterministic_simulation` sets `next.treasury_start = treasury_end` by construction (`:357`). The `RoundLedger` records every term of the real waterfall (`csf`, `total_capex`, `loan_interest`, `side_track_treasury_delta`) and **no invariant ever uses them**.
- **[F] `balance_sheet_balanced` is hardcoded `True`.** `balance_sheet.py:840-846`: retained earnings is a plug, so A = L + E holds by construction, and `diagnostics["imbalance"] = 0.0` is a literal. The one place a cash/accrual leak could have been detected, the answer is written in.
- **[F] `test_repeated_calls_same_input_same_output`** (`test_simulation_integrity.py:835`) reduces its determinism contract to `pure_arithmetic_global = ["round_number"]` — it asserts that adding 1 to an integer works.
- **[F] 2,661 lines named `test_*` collect zero tests** (`test_e2e_full_flow.py`, `test_e2e_multiplayer.py`, `test_full_simulation.py`, `test_shadow_board_e2e.py`, `tests/test_qa_monte_carlo.py`, `tests/test_load_30_facilitators.py`). They are `if __name__ == "__main__"` scripts. `test_qa_monte_carlo.py:557` prints `✅ CERTIFICATION: 10-ROUND LOOP STABLE` and returns 0 regardless of outcome. `test_e2e_full_flow.py` contains zero `assert` statements and wraps 18 of its checks in `if r.status_code == 200:` — a 500 *skips* the check.
- **[F] 18 files call `random.seed()`; zero restore state.** The autouse fixture resets sessions and rate-limit buckets but not the RNG. **[I] high confidence:** the engine tests are order-dependent and intermittently flaky, so a green run is not evidence the next run is green.
- **[F] One real concurrency test** — `test_concurrent_commit_race.py` — and its assertion is `codes.count(201) <= 1`, which passes if *zero* commits succeed.
- **[F] Load tests** (`load_tests/`, k6, 500 VUs, real thresholds) are well written and honestly documented as manual-only. Not in CI.

**Confidence: high.**

### 2.7 Scenario/content authoring

**[F]** Split three ways: (a) `simulation_config.json` — 203 leaf parameters loaded once at `config.py:105-112`; (b) Python literals — `round_configs.py`, `pillar_configs.py`, `healthcare_configs.py`, `verticals/`, `side_tracks/*/configs.py` — deploy-only, with a JSON override layer for the decision matrix; (c) durable per-cohort JSON under `runtime_paths.data_dir()`.

**[F] A new case cannot be authored without a deploy, and the parts that look authorable are not.** The Excel upload path (`admin_router.py:8615-8817`) writes `simulation_config.json` to the **image filesystem** (`runtime_paths.py:24-26` explicitly excludes config files from the durable dir), so it is wiped on redeploy; it hot-reloads five modules but `round_logic.py`, `router.py`, `npc_stakeholders.py`, `turnaround_engine.py` and others bind config constants with `from config import X` at module scope and **keep the old values** — producing a mixed-config process that reports `{"reload": "complete"}`. `config_excel.py` maps 194 of the 203 parameters and omits the CSF pool entirely. The `_engine_tunables` PATCH surface (`admin_router.py:10105-10173`) exposes 24 "engine constants" of which **22 are write-only** — the endpoint returns `{"changed": {...}}` and changes nothing — and 3 of them already contradict `config.py` by a factor of 2.

**[F] There is no config versioning at all.** `grep config_version|schema_version|config_hash` → nothing. `sessions.metadata` stores *identifiers* (`decision_paradigm`, `difficulty_tier`, `region_id`, …) but never the resolved parameter values. **A run from last term cannot be re-derived after the model changes.** You can replay the stored *outcome*; you cannot reproduce it.

**Confidence: high.**

### 2.8 Unknowns — now resolved

Everything in this section was open when I first wrote it. Nine of eleven are now closed, by your answers (§9) and by two benign reads against the live deployment.

| Was unknown | Now |
|---|---|
| Storage backend in production | **[F] PostgreSQL.** `GET /health` → `"database":"postgresql"`, `"demo_mode":false` |
| Durable volume mounted | **[F] Yes.** `/data`, `configured`, `writable`, `durable: true` |
| Swagger exposed in prod | **[F] No.** `/docs` → 404 |
| Railway health check reaches the backend | **[F] No.** `/api/health` → `{"status":"ok","service":"frontend"}`. Confirmed live; upgraded from **[I]** to **[F]** |
| Backups / PITR | **[F] Enabled** (§9.4). Residual: has a restore ever been *rehearsed*? |
| Scores used for grading | **[F] Not yet** (§9.1) — see the framing change in §4.A |
| Cohort scale | **[F] Up to 20 teams per cohort — 20 *committing drivers*, plus up to 5 read-only observers per team** (§9.9, corrected). Multiple cohorts may run concurrently. `MAX_PLAYERS_CEILING = 20` (`player_capacity.py:24`), whose own docstring says *"a cohort larger than this has never been exercised by the round engine's peer-comparison or leaderboard paths"* — so your ceiling **is** the untested edge. `router.py:291` still says 5. **Write concurrency is 20; read concurrency is 20 × (devices per team) — see §4.D, where the two numbers behave very differently.** |
| Which engines run | **[F] All of them** (§9.10). Every one of the 12 unseeded RNG sites is live, including the three the golden trace switches off. |
| Model retuning cadence | **[F] Daily, by you, alone** (§9.7) — the single answer that most re-ranked this plan |
| **[A] still open** | Whether CI is green and gating (branch protection + Railway "Wait for CI" live outside the repo; `ci.yml` is locally modified and uncommitted, and `ci-workflow` is ~694 files stale) |
| **[A] still open** | Whether `WEB_CONCURRENCY` > 1. **[I]** Almost certainly 1 — `scale_preflight` clamps it and nothing suggests an override — but it is worth one look in the Railway **Variables** tab, because at >1 the finding list grows immediately (duplicate `FAC-NNN`/`MUR-NNN`, cohort-quota bypass, `decision_overrides.json` corruption, N× rate limits). **§10.3 explains what the setting is and how to check it.** |

**One consequence deserves its own line.** Production is Postgres; **every test in the repo except the `PG_PARITY` job runs on the in-memory store** (`conftest.py`). Combined with §4.A's ordering divergence, that means the 1,485-test suite and the one golden trace are all validating a business-unit ordering, a `tco2e_emissions` type, and a `get_session_info` aliasing behaviour that **production does not use**.

---

## 3. Top 7 findings, one line each

0. **🔴 Manual and timed pacing gate nothing on the code currently on your disk** — `admin_router.py:3510,3514` reintroduce the raise-only ceiling that `f3f5956` removed today; `tests/test_pacing_gated_modes.py` is 6/6 red. **Uncommitted working tree only — do not push without re-applying.**
1. ~~**`_bypass_password` is a client-settable query parameter — unauthenticated account takeover.**~~ `router.py:810`. Reproduced, **fixed, tested, applied.**
2. **Your daily calibration loop is partly inert and wholly ephemeral** — 22 of 24 `_engine_tunables` are write-only, the carbon-price knob doesn't reach the number students see, hot-reload leaves a mixed-config process, and every redeploy discards the uploaded config. `admin_router.py:10105`, `round_logic.py:2102`, `runtime_paths.py:24-26`.
3. **The run is not reproducible, and 50% of the CEO-interview score can be `random.uniform(-1,1)`.** `admin_shared.py:347` (seed empty by default), 12 unseeded engine RNG sites — **all live, since you run every engine (§9.10)** — and `router.py:5775-5781`.
4. **The client auto-retries a rate-limited commit, and the guard that would stop a double-advance is never sent.** `useSimulation.js:476-487` + `router.py:2100` (`expected_round` has zero frontend call sites).
5. **Round 10 — the finale — is infinitely re-committable and writes no audit-log rows.** `router.py:2092`, `:2599-2608` (`for dec in decisions_raw: pass`).
6. **The financial core has no characterization test, the one conservation invariant is unreachable, and every test runs on a storage backend production doesn't use.** `test_universal_math_engine.py:483`, `balance_sheet.py:844`, `conftest.py` (memory mode) vs. verified production Postgres.

---

## 4. Full review by dimension

### A. Simulation engine correctness and determinism — **CRITICAL**

**Is a run reproducible?** No. **[F]**

- **Seeding is opt-in and empty by default.** `rng_util.py` is *well built* — `event_seed` derives a per-(cohort seed, round, event) integer via SHA-256, explicitly avoiding `hash()` (`rng_util.py:36-46`), and the seed is a facilitator-typed string carried forward in `active_event_flags`. But `admin_shared.py:347` is `"rng_seed": ""`, and `rng_util.py:56` falls back to `random.Random()`. **A cohort run with default settings is fully non-deterministic.**
- **Twelve engine-path sites bypass the seeding layer entirely** and roll on the process-global Mersenne Twister: `impact_engine.py:92` (R5 cyclone), `:164`, `:295` (**R9 strike — zeroes all BU revenue**), `:334`; `org_politics.py:177`; `board_governance.py:251`; `supply_chain_network.py:486-491`; `regulatory_sandbox.py:875` (**$30M flat fine**); `side_tracks/supply_chain/track.py:350`; `npc_stakeholders.py:563,664`; `ending_pathways.py:77` (**which of 5 endings**); `admin_router.py:7227` (**the graded R2 BU**). Three of the owning engines default to **on**.
- **The two backends produce different numbers from identical inputs.** Postgres returns BUs `ORDER BY bu_id` → `[consumer_goods, electronics, pharma, software]` (`database.py:889`); memory returns creation order → `[pharma, electronics, consumer_goods, software]` (`database_memory.py:784`). The engine indexes positionally: `strike_idx = macro_noise["micro_strike_bu_idx"] % len(ctx.new_bus)` (`engine.py:2514-2516`). **Same seed, same decisions, different BU struck.** Plus `database_memory.py:802` truncates `tco2e_emissions` with `int()` on a value the writer rounds to 1 dp.
- **`dry_run.py` reseeds the global PRNG for every live cohort in the worker.** `dry_run.py:119` calls `random.seed(seed)` — process-global — inside a function whose docstring says *"Pure & side-effect free."* Its seed derivation uses `hash(sid)` (`:230`), which is `PYTHONHASHSEED`-randomised and unset anywhere in the repo (verified: three subprocesses gave 514, 288, 224). Mitigating: `run_dry_run` currently has **zero callers** and the route the UI POSTs to does not exist — so the pre-flight simulator 404s today.

**Is round resolution idempotent?** Partially, and the gaps are the dangerous ones. **[F]**

- R1–R9 double-submit is well defended by four overlapping mechanisms (asyncio lock fast-fail, advisory lock, 5s cooldown, `uq_session_round` → translated 409 at `router.py:2615-2622`).
- **R10 is not.** `new_round` is clamped to 10 and persistence switches to in-place `update_latest_global_state`, which has no unique constraint. `fetch_latest_state` still returns `round_number == 10`, so the `current_round > 10` gate never trips, and `game_over` is not set by the normal path. **A second POST five seconds later re-runs `process_tick` on already-resolved terminal state and compounds treasury, emissions and terminal valuation.** The code comments acknowledge the *concurrent* half of this (`router.py:1991-1993`) and miss the sequential half.
- **The retry path creates a genuine double-advance.** `useSimulation.js:476-487` catches 429 and re-POSTs the *same payload* after 5.2s, twice. Sequence: commit #1 succeeds server-side, response lost (proxy timeout, phone flap) → retry → 429 → sleep 5.2s → retry → cooldown expired, lock free, `fetch_latest_state` now returns N+1 → **the same decisions commit round N+1.** `uq_session_round` does not fire (different round number). `expected_round` would catch it — **and the frontend has zero references to it** (verified by grep).
- **Facilitator double-click skips a round.** `unlock_next_round` is a raw `pacing["unlocked_round"] + 1` with no expected-value parameter (`admin_router.py:3587`), reachable from two independent UI surfaces each with its own local busy flag.
- **No idempotency keys anywhere.** The only request-level dedupe in the product is the double-materiality replay bundle (`router.py:3649-3660`, `:4041-4046`) — which is well built and is the pattern to copy.

**Are invariants stated in code?** Declared, then not enforced. **[F]** `_KPI_BOUNDS` exists at `engine.py:300-309` and is referenced **only** inside `apply_side_track_results` (`:378-383`) — `process_tick`'s own output is never checked against it. `grep '^\s*assert '` over non-test backend code returns **zero**. Every engine in `run_new_engines` is `try/except: print("[WARN]…")` and continues (`round_logic.py:592-618` and 22 more), and `process_balance_sheet_tick` mutates `gs["corporate_treasury"]` in place — so an exception mid-function leaves treasury **partially debited** and the round proceeds.

**Numerical soundness.** **[F]** Float everywhere, `Decimal` nowhere (one comment hit). 213 `round()` calls in `engine.py` alone. Divide-by-zero defence is genuinely thorough — sigmoid guards `steepness == 0` *and* `OverflowError` (`engine.py:463-470`), the Gordon-Growth pole is capped (`terminal_valuation.py:307-312`), `/ max(len(x), 1)` is pervasive. **PA/SE disagree with SMP here:** SMP wants `Decimal` for money-like quantities on auditability grounds; PA and SE say deterministic IEEE-754 on a pinned CPython is reproducible, the golden trace already rounds to 4 dp, and the conversion churn across 400+ `round()` sites is not worth it. **Panel outcome: keep float, add the conservation assertion instead.** That is where the real risk is.

**Degenerate inputs.** The commit validation surface is the best-defended code in the repo — duplicate BU ids, missing BUs, unknown BUs, invalid `choice_selected`, `capex < 1`, and an unconditional server-side recompute of `investment_ratio` (`router.py:2216-2290`). **But the no-submit path is unfair. [F]** `_auto_commit_request` (`router.py:352-361`) hardcodes `max(treasury * 0.20, 5_000_000)` instead of the config constants, and defaults to the *display* key `"option_b"` — which is then run through `deshuffle_choice`, and each session has its own `shuffle_seed`. **Two teams that both time out on the same round are auto-committed to different canonical options**, while both are told *"committed with defaults (Option B)"* (`router.py:424`). And the two pacing modes behave oppositely: `free` auto-commit uses the saved draft (`router.py:408`); `timed` auto-commit **ignores the draft entirely** and submits `option_b` / $1 (`admin_router.py:3169-3185`).

**Can you replay a completed run?** **No. [F]** No replay code exists. The decision audit log stores 8 fields and **omits** `dividends_paid`, `pillar_decisions`, `emergency_credit_used`, `engagement_action`, `force_override_cfo` and the recomputed `investment_ratio` — half of `CommitTurnRequest`. R10 logs nothing. `time_to_decision_seconds` is hardcoded `0` by the client (`page.js:794`) — every value in that column is a lie. The Postgres INSERT never populates the `metadata JSONB` column despite `router.py:2571-2576` enriching `player_id` and `investment_ratio` onto the rows *"for audit trail."*

**One thing got materially better and one got materially worse when you answered §9.**

*Better:* **no Muressons score has yet contributed to a grade of record (§9.1).** That converts this from an active academic-integrity exposure into something rarer and more valuable — a closing window. You can fix determinism *before* the first graded cohort, which means you never have to explain a number you cannot reproduce, and you never have to decide whether to re-grade. **[A]** I am assuming the CEO-interview scores have been shown to students as formative feedback; if so, the noise fallback has already told some of them things about themselves that were literally random, which is worth knowing even if no grade moved.

*Worse:* **you run every engine (§9.10)**, so all twelve unseeded RNG sites are live in every run — including `org_politics`, `board_governance` and `supply_chain_network`, the three the golden trace switches off in order to stay green. And **production is Postgres (verified)** while every engine test runs in memory mode, so the BU-ordering divergence at `engine.py:2514-2516` is not a hypothetical: **the micro-strike hits a different business unit in production than in any test you have ever run.**

**SMP's verdict, for the record:** *this is still the red finding, but the framing has changed. It is no longer "you have a problem"; it is "you have one clean shot at not having one." Fix it before the first graded cohort and the question never arises. Ship a graded run first and it arrives permanently.*

**Verdict: Critical.** Bites you the first time a student appeals a grade — and, given §9.7, it is *already* biting you every day: when you retune a parameter and the numbers move, you currently cannot tell whether that was your change or the dice.

---

### B. Domain modelling and expressiveness — **Weak**

**Could a domain expert read one file?** No — but you are closer than most. **[F]** `round_configs.py` (880 lines) and `pillar_configs.py` (1826) *are* a readable declarative case table: per round, `title / theme / crisis / options{a,b,c} / flags_set / impacts / special_rules`. A non-programmer could read that.

**The declarative/imperative seam leaks, silently. [F]** `_apply_common_impacts` (`round_logic.py:1173`) is the generic applicator, and it reads only `carbon_intensity_delta`, `revenue_delta`, `governance_risk_delta` and `reputation`. The config table *also* uses `reputation_delta` (6 occurrences) — applied by two other hand-written paths (`round_logic.py:1796`, `impact_engine.py:232`). `treasury`, `social_license_delta` and `natural_capital_debt_delta` are likewise per-round hand-applied. **[I] high confidence:** adding `reputation_delta` to R1/R4/R7/R8 silently does nothing; adding both keys to R6 double-applies. A designer editing the table cannot predict which keys are live.

**A rule that is advertised four times and unreachable in play. [F]** `round_logic.py:1834-1852` charges the EU AI Act ongoing cost when `ai_monetised` is in `prev_flags` and round ≥ 7 — but the block lives inside `_post_r6_ai_bias`, which `_POST_TICK_MAP` dispatches **only for round 6**, and `prev_flags` is the previous round's, so on the round the player picks Monetise the flag isn't there yet. Meanwhile the option text, the teleprompter (`admin_teleprompter.py:187`), `terminal_valuation.FLAG_DEPENDENCY_GRAPH:661` and the student glossary all promise costs from R7 onward.

**Rule duplication — the divergences that are already live. [F]**

| Rule | Copies | Status |
|---|---|---|
| **CSF pool** (`treasury × 0.20`, floor $5M) | `config.py:143-145` (constant), `router.py:2284` (**wins for manual commits**), `router.py:360` (**hardcoded literal — wins for auto-commits**), `page.js:389-400` (display) | Both config keys are **absent from `simulation_config.json` and `config_excel.py`** — permanently unauthorable. Three teams in a cohort can be scored on two different pools. |
| **Shadow carbon price ($250/t)** | `config.py:134` (authorable, feeds CAROIC only), `round_logic.py:2102` `special.get("carbon_tax_per_ton", 250)` (**wins for terminal carbon cost**), + 5 more literals | Editing the Excel parameter and seeing a green "1 change" diff changes **nothing** the students see. Config theatre. |
| **`_engine_tunables`** (24 "engine constants", super-admin UI) | `admin_router.py:10105-10173` | **22 of 24 are write-only.** 3 already contradict `config.py` by 2× (`competitor_growth_rate` 0.03 vs 0.06; `greenwashing_penalty` 8.0 vs 15.0; `vrio_imitation_decay_rate` 0.05 vs 0.10). The other 2 win over config via `_god_mode_settings`, making the `simulation_config.json` values dead. |
| **M_R reward function** | `terminal_valuation.py:175-256` (**wins**) + `round_logic.py:2116-2128` (comment inside the authoritative function, says +0.30 and max 2.08) + `TechnicalGlossary.js:273-297` (says +0.30, max 1.65) + `SustainabilityBalancedScorecard.js:2088` (says Community Fund earns **both** bonuses, +0.30 — the backend is `if/elif`, so **+0.18 only**, overstated by 67%) + `mrJourney.js` (missing `civil_water_priority` blocker; mis-attributes `early_decarboniser`) | **Students are being taught a reward function the engine does not implement.** |
| **10-round case catalog** | `round_configs.py` ↔ `SustainabilityBalancedScorecard.js:2027-2091` (65-line hand mirror shown to players at game end) | **Already diverged** — R6 option letters are swapped and the amounts wrong. `frontend/__tests__/war-map-model.test.js:12-18` documents removing exactly this pattern for the war map; the lesson wasn't carried across. |
| **Workforce readiness deltas** | `config.py` (`HIGH=16.0, MEDIUM=8.0, NONE=-10.0`) ↔ `admin_analytics.py:799` glossary (`+8 / +4 / -5`) | **Every value in the facilitator-facing glossary is exactly half the engine's.** |
| **R1/R2 mandatory gates** | `page.js:1001` only | **Server enforces neither.** The quiz gate *is* server-enforced (`router.py:2146`), so the pattern exists — the other two were never added. A direct POST skips both minigames. |
| **Archetype ladder (1.8/1.2/0.8)** | 9 copies | Currently all agree. |

**Tripwires that exist and work:** shockwave catalog, `ROLE_HIERARCHY`, decision paradigms. **Tripwires cited in comments that do not exist:** `admin_analytics.py:135` names `backend/tests/test_player_visibility_catalog.py` — **that file is not in the repo.**

**`validation_logic.py` (1001 lines) is imported by no module.** `grep -rn "validation_logic" --include=*.py` returns nothing. Despite the name it is an E2E HTTP traversal harness, not a validator.

**Verdict: Weak.** The declarative core is a real asset; the imperative sprawl around it and the six live frontend/backend divergences mean a rule change is neither small nor safe today.

---

### C. State, concurrency and transactional integrity — **Weak**

**[F]** Covered in §2.5. The specific races, as they actually behave today:

| Race | Today |
|---|---|
| Two players, same team | **Safe.** One driver credential per session; observers refused at `router.py:258-264`. |
| Submit vs round close | **The optimistic lock is dead code** (`expected_round` never sent). What actually stops a late submit is a pacing gate reading a **process-local dict** with a documented 3-second cross-worker staleness window (`coordination_store.py:57`). |
| Facilitator double-click advance | **Skips a round** (`admin_router.py:3587`). Recoverable via `relock_round` — unless a team has already committed, then it isn't. |
| Retried request → duplicate submit | **Double-advances the round.** See §A. |
| Two facilitators on one run | **Undo takes no lock at all** (`admin_router.py:9019`) — a player commit racing an undo builds round 8 on a deleted round 7. **God-mode freeze is global, not per-cohort** (`admin_shared.py:292`) — one facilitator freezing their room 503s every concurrent classroom. |
| `update_session_metadata` | **[F]** `database.py:362-378` is a `SELECT`-then-`UPDATE` across an await with no transaction and no `FOR UPDATE`. This is the write path for `allowed_player_ids`, `registered_players`, `max_round`, `end_date`, `is_public`, `deleted_at`. **Any two concurrent metadata updates lose one.** |
| Undo / reset / hard-delete | **[F]** All three run `ALTER TABLE … DISABLE TRIGGER` **inside** their transaction (`database.py:1367-1370`, `:1607-1613`), which takes an `ACCESS EXCLUSIVE` lock table-wide. **Every commit in every cohort on the instance blocks** for the duration. The cohort reset recurses over children in **N+1 separate transactions** (`database.py:1702-1705`) — a failure at child 11 of 20 leaves the cohort half-reset with no rollback. And practice-mode reset invokes this **from inside `_commit_turn_impl` while holding the advisory lock and its pool connection** (`router.py:2667`). |

**Two silent-write bugs from the two-backend divergence. [F]** `get_session_info` returns a **live store dict** in memory mode (`database_memory.py:655`) and a **fresh dict built from JSON** under Postgres (`database.py:681-699`). Three call sites mutate the returned dict and never write back: `router.py:6175` (`max_round` pace lock — read back at `router.py:2116`), `router.py:6194` (`round_deadline`), `router.py:2790` (facilitator commit-notification feed, read at `router.py:6204`). **Under Postgres these three features silently do nothing.** Under memory they mutate the store but never call `_persist()`, so they die at restart. Broken in both modes, differently.

**`_fa_force` is reverted by the app itself. [F]** `force_advance_cohort` (`admin_router.py:3389-3407`) sets `pacing["_fa_force"] = True` and — verified by grep — is the **only** pacing mutator that does not call `mark_pacing_dirty`. But `_fa_force` **is** part of the serialised policy (`admin_shared.py:1522-1527`), so under Postgres the shared row still says `False`, and the 3-second background refresher (`coordination_store.py:281-289` → `restore_pacing_policy`) copies it back. **The facilitator presses Force Advance, gets `{"status":"ok"}`, and within 3 seconds nothing happens.** (Single-worker memory mode is unaffected — this bites the moment you go to Postgres.)

**`_next_player_id` is never restored. [F]** Defined twice (`admin_shared.py:1355`, shadowed at `admin_router.py:3670`), incremented at three sites, restored nowhere. After any restart, `induct_player` and bulk upload mint `MUR-001` again, colliding with live credentials.

**Verdict: Weak.** Single-worker + per-session locks is a defensible architecture for this scale, and the panel would keep it. What is weak is that several features silently assume a shared world they do not have, and the two-backend split has produced real behavioural divergence rather than just maintenance cost.

---

### D. Resilience — the run-day drill

| Scenario | What happens today | Verdict |
|---|---|---|
| **Server restarts mid-round, live cohort** | Postgres state survives; pacing and freeze rehydrate; the unlock gate is **time-derived** and therefore restart-safe (`admin_shared.py:1443-1493` — genuinely well designed). The in-flight commit is lost; the player sees a raw `Failed to persist round: {asyncpg exception}` and must re-click. **[F] Silent hole:** the `_scheduled_unlock_task` timer is never re-armed, so **in `timed` pacing the auto-commit of stragglers never runs again** — the round unlocks and uncommitted teams are simply left behind, with no log line and nothing on the facilitator dashboard. All morning's facilitator notes, annotations, bonuses and peer evaluations are gone (process dicts, both backends). | **Fail silent** on the timer + facilitator work product; fail safe on game state |
| **DB briefly unavailable during resolution** | No partial round (`insert_next_round` is one transaction). HTTP 500 with the **raw asyncpg exception text in the player's toast** (`router.py:2614-2625`). Pool exhaustion specifically is handled well — clean 503 with a remedy (`database.py:302-312`). **[I]** `get_pool()` caches `_pool` globally and never recreates it, so a hard connection loss likely 500s until process restart. | **Fail loud, leaky** |
| **Player laptop sleeps 10 min** | Poller resumes, force-syncs. If auto-committed under **`free`**, the saved draft is used. Under **`timed`**, `_auto_commit_player` **ignores the draft** and submits `option_b`/$1 (`admin_router.py:3169-3185`). Two pacing modes, opposite data-loss behaviour, same button. | **Fail silent (data loss)** |
| **WebSocket drops for half the cohort** | `ws.onerror = () => {}` (`page.js:886`); reconnect after 5s; nothing shown. Round advance is covered by the REST poll, so mostly harmless. **Permanently lost:** universal broadcasts, shockwave overlays, `auto_committed` notices — push-only, no replay. **[F] No ping/pong on either side** — a half-open socket on venue wifi is never detected by either end. | **Fail silent** |
| **A team never submits, deadline passes** | `free` + timeout > 0: enforced lazily on any teammate's poll — robust, no timer dependency, uses the draft. `free` + timeout **0 (the default**, `admin_shared.py:1427`): **the barrier never releases** — one absent team deadlocks the cohort until Force Advance. `timed`: auto-commit with `option_b`/$1, **unless the server restarted**, in which case nothing happens. | **Fail silent** |
| **Facilitator advances by accident** | Force-advance auto-commits every uncommitted team within ~1-2s. **No `_audit()` call.** Recovery is `undo-round` — which is **also unaudited** and **permanently deletes the `decision_audit_log` rows** for the undone round (`database.py:1372-1393`), and takes an `ACCESS EXCLUSIVE` lock that briefly blocks every other cohort. The accident and the fix both leave no record. | **Fail silent** |
| **Two facilitators / a TA act at once** | Ownership checks exist and are correct where applied — **and are applied to roughly 30 of 232 admin endpoints.** Undo takes no lock. Freeze is global. | **Fail silent** |
| **Slow, flaky venue wifi all session** | **The worst case in the set. [F]** The 5-second poller is a *separate raw fetch* whose catch block is `catch { /* silent */ }` (`useSimulation.js:686`) and which **never touches `connectionState`**. `ConnectionBanner` is rendered but only ever driven by `fetchDashboard`, which is event-driven. **A player sitting on a round with the backend down sees a frozen, confident-looking board and no banner at all.** Commit failures produce a 0.75rem toast at `bottom: 40px` that the next dashboard fetch clears (`useSimulation.js:234`). A successful-but-lost commit reports "failed" (409) while it succeeded. | **Fail silent — critical** |
| **Scenario config has an unexpected value** | Malformed JSON → caught, one stdout line, `SIMULATION_CONFIG = {}`, **every economic parameter silently reverts to its hardcoded default**. Valid JSON with a wrong type (`"rounds": "ten"`) → `int()` at module top level → the app does not boot. **No schema validation anywhere.** | **Fail silent** (the more likely case) |
| **Largest cohort, all submitting in the last 30s** — sized from §9.9 as corrected: **20 committing drivers**, plus up to 5 read-only observers per team | **The write path and the read path have to be priced separately, and only one of them cares that observers can't commit.** <br><br>**Writes — 20, and this number is unchanged by the correction.** `DB_MAX_CONNECTIONS=40`, each in-flight commit holds ~2 connections (advisory lock + work) → **20 concurrent commits consume the pool exactly.** **[I] CPU is the harder wall:** `process_tick` is synchronous and there is **no `run_in_executor`/`to_thread` anywhere in the backend**, so at `WEB_CONCURRENCY=1` all 20 ticks serialise on the event loop — and decision-regret runs `process_tick` **two extra times per commit** (`router.py:2740-2752`), on by default, so it is effectively **60 serial ticks** in the last 30 seconds. That is the binding constraint, and 20 drivers is enough to hit it. <br><br>**Reads — driven by connected browsers, and you have confirmed observers use their own laptops (§9.9). [F]** An observer signs in with `MUR-004-VIEW`, resolves to the **same `session_id`**, and lands in the same cockpit read-only (`router.py:191-215`). `GET /dashboard` is the **one** route opened to them (`allow_observer=True`, `router.py:1868` — the only such opt-in in the file), and the 5-second poll at `useSimulation.js:640-690` **has no observer gate**. So **20 teams × 6 laptops = ~120 full-rate pollers** at full scale. Every poll runs `_cohort_commit_progress` unconditionally (`router.py:1901`), which does one `fetch_latest_round` **per sibling** — 20 queries — plus `get_session_info`, `fetch_latest_state` and the full history. Call it **~23 queries per poll**. 120 devices ÷ 5 s = 24 polls/s → **≈ 550 queries/second**, purely to render the "X/Y committed" badge, before anyone commits anything. *(I am correcting my own earlier figure of ~960 q/s downward: `_cohort_advance_status` receives `_committed`/`_teams` as arguments at `router.py:1910` and does not recompute them on the normal path. It does recompute — another 20 queries — on the auto-commit branch at `:512`.)* Note also that `_cohort_commit_progress`'s own docstring still says *"the cohort is capped at 5 players"* — 4× stale. **The redundancy is the opportunity:** all six observers on a team run the *identical* 20-sibling scan, and so does every other team. One per-cohort cache with a 2–3 s TTL collapses ~550 q/s to under 10 — see #46. | **Fail loud at the DB, fail hard at the CPU.** Not survivable at 120 devices without #33 and #46. |
| **An observer refreshes their board** *(new — found while checking your §9.9 correction)* | **[F] A read-only seat has a write side effect on another team's game.** `get_dashboard` is observer-readable, and it calls `_cohort_advance_status` (`router.py:1910`), which calls `await _auto_commit_laggards(parent, max_r)` (`router.py:508`) — **the barrier and the free-advance timeout are enforced on the read path, by whoever polls first.** So a spectator's browser can be the thing that force-commits a *different* team's round with that team's saved draft. The seat is fail-closed on all 27 other player routes and correctly refuses every mutation; the mutation happens anyway, one call frame down, because a GET was given a side effect. Conversely, if nobody polls, **Force Advance and the round timeout never fire at all** — the 5-second poll is the de-facto scheduler. | **Fail silent, wrong actor** |
| **Two or more cohorts running simultaneously** (§9.9) — **a scenario I did not originally price** | **[F] Three platform-global controls turn one facilitator's action into every other cohort's incident.** (i) `_god_mode_settings["system_frozen"]` (`admin_shared.py:292`) is **one dict for the whole platform**, read at `router.py:2057-2063` — freezing your room 503s every commit in every concurrent classroom. (ii) `finale/ring-bell` calls `manager.broadcast_students(...)`, and `admin_ws.py:96-99` iterates **all** `active_connections` ignoring cohort — cohort A's bell interrupts cohort B mid-decision. (iii) `undo-round` / `reset` / `hard-delete` run `ALTER TABLE … DISABLE TRIGGER` **inside** their transaction (`database.py:1367-1370`), taking `ACCESS EXCLUSIVE` on all three round tables — **every commit in every cohort blocks** until it finishes, and a 20-team cohort reset is 21 sequential such transactions. Worse, **`_god_mode_settings` carries live engine parameters** (`overrun_probability`, `overrun_severity`, `global_carbon_fee`, `market_hostility_index`, `industry_vertical`) that `engine.py:2616-2621` reads *mid-tick*, and they are settable by any run-managing facilitator — **so one facilitator's slider silently changes another cohort's economics mid-round, with no trace in either run's record.** | **Fail silent, cross-tenant — critical at your stated scale** |

**Two delivery-layer facts that make all of the above worse:**

**[F][critical] Railway cannot detect a dead backend — verified against production.** `railway.json` sets `healthcheckPath: "/api/health"`. `frontend/app/api/health/route.js` is a static App-Router handler returning `{status:"ok", service:"frontend"}`, and Next.js applies array-form `rewrites()` as `afterFiles`, so the filesystem route wins. I confirmed this live on 2026-08-02: **`GET https://cso.mastersustainability.org/api/health` → `{"status":"ok","service":"frontend"}`**, while `GET /health` (which *is* rewritten) reaches the backend and returns the real payload. The backend's own `/api/health` — annotated *"railway.json healthcheckPath — must exist"* (`main.py:499`) — is unreachable from outside. `docker-start.sh:65-71` states the exact opposite as its design rationale. A backend crash-looping on `sys.exit(1)` restarts every 3s forever inside `docker-start.sh:32-49` while Railway reports the deployment **healthy** and never cycles it. **This is not a latent defect; it is the state of your production monitoring right now.**

**[F][high] `deploy_preflight.py` is dead code.** 186 lines of well-designed boot checks. `grep run_preflight` finds only a test. `PREDEPLOY_CHECKLIST.md` Layer 4 tells the operator to look in the logs for `[preflight] Deployment configuration looks correct.` — **a string that can never appear.**

**Verdict: Critical.** Not because any single item is catastrophic, but because the dominant failure mode across the whole table is *silent*, and you have told me silent failure on run day is the worst outcome.

---

### E. Data integrity, auditability and recovery — **Weak**

**What's genuinely good. [F]** The immutability triggers (`database.py:184-238`, mirrored in `db/init.sql:122-172`) block all DELETE on round tables and permit UPDATE only on the max-round row per session. `decision_audit_log` is strictly append-only. `uq_session_round` prevents duplicate rounds. This is real, it works, and it is the thing that makes the round history trustworthy.

**Where it breaks. [F]**

1. **R10 writes no audit rows.** `router.py:2606-2608` — the comment says *"Still log R10 decisions to the audit trail"* and the loop body is `pass`. The finale decision that terminal valuation and archetype hang on is not recorded.
2. **`time_to_decision_seconds` is hardcoded `0`** by the client (`page.js:794`). There is no timing data for any run, ever.
3. **The Postgres audit INSERT drops `metadata`.** `database.py:1148-1167` writes 8 columns; `metadata JSONB` (`init.sql:102`) is never populated, discarding the `player_id` and `investment_ratio` that `router.py:2571-2576` deliberately enriched *"for audit trail."* Memory mode **does** store `player_id`.
4. **A `lead_facilitator` can rewrite a cohort's live KPIs with zero trace.** `POST /{session_id}/override` (`admin_router.py:6174-6248`) mutates treasury / reputation / social licence in place and calls `_audit()` **nowhere**. The only records are a WebSocket push and an entry in `_session_messages` — a process dict.
5. **`undo-round` deletes the append-only log, unaudited.** `admin_router.py:8968-9043` → `database.py:1372-1393` disables the trigger and `DELETE`s. Supports `cohort_wide=True` and multi-round rollback. No audit entry.
6. **~87 of ~141 mutating admin endpoints have no `_audit()` call** (script-derived, treat the number as ±). The unaudited set includes `force_advance_cohort`, `set_pacing`, `unlock_next_round`, `relock_round`, `delete_session`, `patch_session_metadata`, `set_bu_composition`. `db/admin_audit.jsonl` is 1,858 lines, overwhelmingly logins.
7. **All facilitator work product is process-memory only, in both backends.** `_facilitator_notes`, `_annotations`, `_student_bonuses`, `_peer_evaluations`, `_session_messages`, `_broadcast_history`, `_god_mode_audit_log`. The memory snapshot does not serialise any of them; Postgres persists none of them. **A restart erases every note, annotation, bonus and peer evaluation of the day** — including assessment data.

**Backup and restore. [F] There is no procedure and no tested path.** `grep pg_dump|pg_restore` → zero hits. `DEPLOYMENT_CHECKLIST.md` and `PREDEPLOY_CHECKLIST.md` do not mention backup. `COMPREHENSIVE_AUDIT.md:118-136` says it outright: *"point-in-time recovery is OFF. No volume backup schedule. Zero backups exist."* and *"You lost a database once already this week."* **[A]** I cannot tell whether that was fixed.

**The only "backup" feature in the product is broken under Postgres. [F]** `GET /god/export` (`admin_router.py:9904-9930`) reads `db._sessions`, which under Postgres is a metadata cache with no `global_state` key — so every exported session reports `current_round: 1, treasury: 0`. No round states, no BU states, no decision log. `POST /god/import` writes back into that same in-process dict — a no-op that evaporates on restart.

**The one genuinely engineered recovery path is the one production is not supposed to use:** `database_memory._persist` (write-to-tmp → rotate to `.bak` → atomic replace with retries) and `_load_from_disk` (quarantine corrupt primary with a timestamp, fall back to `.bak`, refuse to start silently empty). Covered by `tests/test_res1_snapshot_resilience.py`.

**Migration safety. [F] No Alembic, no version table, no down-migrations.** Schema exists in **two hand-maintained copies** (`db/init.sql` and the auto-schema in `database.py:92-240`) kept in sync **by a code comment** — with no tripwire test, in a repo that has tripwires for the role ladder and the shockwave catalog. `CREATE OR REPLACE FUNCTION fn_immutable_guard` runs on every boot, so a rolled-back deploy silently reinstalls old guard semantics over data the newer code wrote. **[I]** The deeper fragility is that all game state is schemaless JSONB with no version stamp: an engine change that renames a flag makes every prior round's flag unreadable, with no error — the reader sees `None` and falls back to a default.

**Multi-tenancy. [F] By convention, not provably.** `owns_session` / `_assert_session_ownership` exist and are correct — and are applied to ~30 of 232 admin endpoints.

**Verdict: Weak.** The append-only spine is right. Everything hanging off it — the audit trail, the facilitator record, the backup story — is not there yet.

---

### F. Security and privacy — **Critical**

**The auth foundation is better than the endpoint surface.** **[F]** Facilitator auth is solid: HS256 JWT in an `HttpOnly; Secure; SameSite=strict` cookie, re-validated against the registry on every request with a `ver` claim as a revocation kill-switch (`admin_router.py:63-121`); the `X-Facilitator-Id` header fallback is genuinely gone; `JWT_SECRET` auto-generates to a 0600 file when unset. Prompt-injection defence in `llm_negotiator._parse` (`:99-129`) is textbook — schema-constrained output, enum-validated mood, whitelist-validated concession, scripted fallback, and offers re-validated on a separate POST. XSS is well handled: DOMPurify with an explicit allowlist behind every backend-content sink, CSP `default-src 'none'` on API responses, CORS an explicit origin allowlist with enumerated methods. Backend dependencies are fully pinned with a documented `pip-audit` remediation pass.

**Then:**

**[F][CRITICAL] `_bypass_password` is a query parameter.** `router.py:810`:

```python
async def join_session(session_id: str, req: JoinSessionRequest, _bypass_password: bool = False):
```

FastAPI binds a non-path, non-Pydantic scalar with a default as a **query parameter**; a leading underscore is not filtered. The comment three lines below says *"`_bypass_password` is set ONLY by `player_login` … never from an HTTP body, so it cannot be used to skip a driver's password"* — which is true and irrelevant, because it comes from the query string. **I reproduced this on FastAPI 0.141.1** (see Exemplar 1). The only remaining gate is `validate_player_id`, which is membership, not authentication.

**[F][CRITICAL] The player authz pair is published unauthenticated.** `GET /api/admin/cohort-pulse/{cohort_id}` (`admin_router.py:11233`) has **no `Depends`** and returns every team's `session_id`, `player_id`, name and full KPI history. Player auth for REST is a string comparison of the `X-Player-Id` header (`router.py:251-254`). Chain: `GET /public/join/{code}` is unrate-limited over a ~1.7M code space → cohort id → `cohort-pulse` → every `(session_id, player_id)` → **read or write any team's decisions before reveal**.

**[F][High] `GET /api/admin/players` returns every player's plaintext password, platform-wide.** `admin_router.py:3793-3794` pops `password` (the bcrypt hash) and **not** `plaintext_password` (written at `:4018`, `:5026`, `:5104`). Guard is `require_facilitator` — which admits `project_admin` — and there is **no tenancy filter**. The `/leaderboard` route has a careful projection (`_roster_view`); `list_players` has none.

**[F][High] `GET /api/admin/sessions` takes `facilitator_id` as a caller-supplied optional filter**, not from the JWT (`admin_router.py:4930`). Omit it → every cohort on the platform, with `registered_players` verbatim (names, emails, passwords).

**[F][High] ~25 admin endpoints have no guard at all**, including `/{session_id}/debrief` (round-by-round decisions across all child sessions), `/{session_id}/peer-evaluations` (named student ratings — PII), `/{session_id}/bonuses`, `/annotations/{session_id}` (**returns entries marked `visible_to_students: False`**, which the player-facing route filters), and **all 16 `admin_teleprompter.py` routes** — the facilitator's script, talking points and per-option anchors.

**[F][High] ~60 session-scoped admin routes lack `_assert_session_ownership`**, including `POST /{cohort_id}/shockwave` (apply treasury+reputation damage to *any* cohort), `POST /{session_id}/generate-player` (mint a credential in any cohort, plaintext returned), and `PATCH /sessions/{session_id}/metadata` where `facilitator_id` is in the `EDITABLE` set — **any lead facilitator can reassign ownership of any pre-start cohort to themselves.**

**[F][High] `POST /api/simulations/set-username` is unauthenticated identity mutation** (`router.py:541`). Body `{user_id, role, username}`; `role: "facilitator"` rewrites a registry facilitator's username and persists it — and `facilitator_login` matches on username.

**[F][High] The quiz answer key is served unauthenticated.** `GET /api/simulations/quiz/{notebook_id}` (`router.py:4452`) returns `"correct"` and `"explanation"`. Notebook ids come from the equally unguarded `/admin/resources/notebooklm`. Quiz completion feeds `learning_bonuses_awarded` and the mandatory-quiz gate. **This is the clearest "the UI is the security control" case in the codebase.**

**[F][Medium] `finale/ring-bell` broadcasts to every player on the platform** (`admin_ws.py:96-99` ignores cohort). Cohort A's bell freezes cohort B's screens.

**[F][Medium] Retention is configured but never executes in production.** `session_reaper.py:99` wraps *both* the solo reap and the `data_retention_days` reap in `if _memory_backend_active():`. Under Postgres — the documented production setting — a cohort configured with 30-day retention is **never** deleted. The setting is validated and unit-tested against the memory backend only.

**[F][Medium] Rate limiting exists and is well built** (sliding window, correct trusted-proxy CIDR parsing, per-IP *and* per-player-id buckets for login, persisted bans) — with only **8 call sites**. Unprotected: player `POST /change-password` (an unauthenticated password oracle taking `{player_id, old_password}`), `/public/sessions/{id}/join` (a second oracle), `/public/join/{code}` (enumeration), `/solo-start`.

**PII / FERPA / GDPR. [F]** Stored per student: id, name, email, every decision, journey and reflection free text, CEO-interview transcripts and LLM assessments, named peer evaluations, consent timestamp. Consent capture exists and is per-cohort. **Art. 15 access exists twice** and is done properly (self-service `GET /{session_id}/export-my-data` is SEC-3-bound and excludes credentials; `GET /god/gdpr-export/{player_id}` is super-admin). **There is no Art. 17 erasure path for a data subject** — facilitator delete is a soft delete, session hard-delete is cohort-wide and super-admin-only, and there is no per-player hard delete. Combined with the dead retention reaper, effective retention is indefinite.

**Verdict: Critical.** Finding 1 alone is a run-day and a reputational event. The systematic gap is not the *role* dimension — that is applied consistently and correctly per `CLAUDE.md` — it is the **second dimension: which cohort.** That gap is closeable with two tripwire tests (see Remediation #7).

---

### G. Testing strategy — **Weak, with one excellent asset**

Covered in §2.6. What a great suite for *this* system looks like:

1. **A financial golden trace.** Clone `test_stakeholder_golden_trace.py` onto the money surface — same seed, same 10-round script, capture `corporate_treasury`, `historical_ebitda`, `tco2e_emissions`, `synergy_multiplier`, per-BU `revenue_base`/`opex_base`/`carbon_intensity`, plus final `calculate_mr` and `calculate_terminal_value`. **The mechanism already exists and demonstrably works — it was simply never pointed at the financials.** Highest-value item in this entire review by a wide margin.
2. **The treasury waterfall conservation equation.** `RoundLedger` already records every term. Replace the unreachable continuity check with the real equation (Exemplar 3).
3. **A *collected* full R1→R10 HTTP scenario test** — port `test_e2e_full_flow.py` into `backend/tests/` as real pytest functions, patch `_commit_timestamps` instead of `time.sleep(5.2)`, delete every `if r.status_code == 200:` guard, and assert *values* at game over.
4. **`balance_sheet.py` unit tests** — 943 lines, exercised by one integration touch. `check_covenants`, `calc_stranded_assets`, `calc_environmental_provisions`, `calc_brand_value` have zero direct tests, and covenant status drives insolvency.
5. **RNG hygiene + a real determinism contract** — an autouse fixture that snapshots/restores `random.getstate()`, plus a test that `process_tick` with a set seed is bit-identical across two calls on *every* numeric field and differs when the seed changes.
6. **Two guard tripwires** (Remediation #7) — every `@admin_router` route has a `Depends(require_*)`; every route whose path contains `{session_id}`/`{cohort_id}` calls `_assert_session_ownership`. These close a whole class permanently, the same way `test_role_hierarchy_sync.py` does.

**Verdict: Weak** in coverage of what matters, **Strong** in test *infrastructure discipline* — `conftest.py` is the best file in the repo, and `test_suite_does_not_touch_real_state.py` (a test that tests the conftest) is the kind of thing most teams never write.

---

### H. Code quality and craft — **Adequate**

**Complexity hot spots. [F]** `admin_router.py` 12,492 lines / 232 endpoints / 55 responsibility sections / 31 Pydantic classes. `router.py` 6,987 lines / 73 endpoints, dominated by `_commit_turn_impl` at **776 lines**. `round_logic.py::_post_r10_grand_finale` at **766 lines**. `engine.py`'s four stage runners at 508 / 492 / 453 lines. `ExecutiveCockpit.js` at 4,597 lines.

**Error handling. [F]** **Zero bare `except:` anywhere in the backend** — genuinely good hygiene. The problem is placement, not syntax. Counts of `except Exception`: `admin_router.py` 67, `router.py` 64, `round_logic.py` 25. The ten that matter, in order:

1. `router.py:2479-2488` — **the entire new-engine batch is one swallow, on the commit path.** Balance sheet, board governance, supply chain, NPC stakeholders, org politics, biodiversity, autonomous agents. The round commits `201` with those ledgers silently absent; the player sees a normal results screen with different numbers.
2. `round_logic.py:589,617,635,677,…` — **23 further per-engine swallows inside `run_new_engines`**, each a raw `print("[WARN] …")`. Double-swallowed with #1.
3. `admin_router.py:2700,2727,2751` — **`refresh_token` swallows cookie-issuance failure and returns `{"status":"refreshed"}`.** The facilitator is told their session was extended; it wasn't; they get logged out mid-workshop.
4. `admin_router.py:4045-4046` — `register_player`'s durable write is `except Exception: pass  # Non-critical`, and the endpoint still returns 200 with the credential. The facilitator hands a student a login that may not survive a restart.
5. `admin_router.py:3747-3748` — intervention config persistence swallowed, 200 returned.
6. `admin_router.py:3273-3274` — `_auto_commit_player` catastrophic swallow; the scheduler unlocks the next round anyway. A team is silently left behind.
7. `router.py:429-430` — same class on the Force-Advance path a facilitator presses live.
8. `router.py:2769-2770` — decision-regret shadow tick, `except Exception: pass`.
9. `admin_router.py:9443-9444` — audit-log write failure swallowed. Right priority, but no counter and no alternate sink: a full volume silently ends the forensic trail.
10. `config.py:104-109` — malformed config → one `print`, `SIMULATION_CONFIG = {}`, **every economic parameter silently reverts to default.**

**[F] The round-resolution path does not use the logger at all.** `round_logic.py` has 21 raw `print()` calls and no `getLogger`. In JSON log mode those lines are not JSON. So every engine failure during round resolution is unstructured stdout with **no request id, no session id, no cohort name** — in a codebase that built a genuinely good request-correlated structured logger and then didn't wire the most important path into it.

**Type system. [F]** Illegal states are freely representable. No mypy/pyright config, no TypeScript. `TickContext` is the closest thing to a domain type and it is a mutable bag. **PA:** *this is where the eighteen-month cost lives — not in the line counts.*

**Comments. [F]** Unusually good on *why* — `database.py:167-182` explaining the trigger incident, `conftest.py` documenting BUG-2026-07-28 with a standing "do not add an unlink here" instruction, `scale_preflight.py:4-9` explaining the worker gate. **And several of the most load-bearing comments are now false:** `round_logic.py:2116-2128` states +0.30 synergy and max 2.08 *inside the function that computes +0.15 and 2.05*; `engine.py:632` mis-states the workforce bonus; `router.py:842-844` asserts the `_bypass_password` safety property that Finding 1 disproves; `router.py:291` says the cohort is capped at 5 (it's 20); `docker-start.sh:65-71` states the opposite of what the health check does.

**Verdict: Adequate.** The craft is real. The failure mode is that the comments and docs are a layer of *intent* that the code has drifted out from under, and in a one-person codebase that drift is invisible until someone else reads it.

---

### I. Observability — **Weak**

**[F]** `logging_config.py` is a genuine structured logger — JSON in prod, ContextVar-carried `request_id` + `session_id`, `X-Request-Id` echoed. `main.py:446-466` emits exactly one access line per request **with latency**, and because the session id is regex-derived from the path, **commit and dashboard latency are already measured and correlated per session.** That is the single best observability asset here and it is nearly free to exploit.

**[F]** And then: no metrics endpoint, no Sentry, no OTel, no statsd (`requirements.txt` is 16 lines; repo-wide grep is clean). Nothing measures error rate, DB latency or pool saturation. `coordination_store.publish_failure_count()` exists and is exposed by nothing.

**Can an operator answer "is this run healthy right now?" without SSH? No. [F]**
- `/health` answers "process up, storage durable" — nothing about a run.
- **The god-mode "System Health" chip is hardcoded green.** `god-mode/page.js:444`: `const isOptimal = live && (status.system_memory_mb || 0) < 500;` — and `system_memory_mb` comes from a `try: import psutil` (`admin_router.py:9726-9731`) where **`psutil` is not in `requirements.txt`** and the Dockerfile installs only that file. The `except` returns `0`. `0 < 500` → **always 🟢 Optimal whenever the backend answers at all.** It is a liveness probe wearing a health badge. (Credit: the surrounding `live`/`stale`/`unreachable` tri-state is well built and refuses to fabricate zeros during an outage. The one metric feeding "Optimal" is just dead.)
- **`SessionHealthDashboard` is not system health** — it scores *simulation* state (treasury < 0 → critical). A cohort throwing 500s on every commit shows 🟢 healthy.
- **A plain facilitator can see nothing at all.** `SessionHealthDashboard`, `GodModeStatus` and `SystemContextBar` are god-mode-only; `facilitator/page.js` imports none of them.

**Verdict: Weak** — but cheaply fixable, because the hard part (structured, correlated, latency-bearing request logs) is already built.

---

### J. Delivery and change safety — **Weak**

**[F]** CI exists (4 jobs including a real Postgres parity gate). **[A]** Whether it is green and gating is outside the repo — and `.github/workflows/ci.yml` is locally modified and uncommitted, which is a smell.

**[F] You can deploy while a session is live and nothing stops you.** The only control is prose: `DEPLOYMENT_CHECKLIST.md:8-9` — *"A git push to the deploy branch restarts the container. Do not push during a live session."* No gate, no live-session check, no CI hook.

**[F] Maintenance lockout exists but is narrow and manual.** `POST /god/freeze` sets `system_frozen`, broadcasts, **and is audited**. It blocks `commit-turn` with a 503 and a player-facing message. It does not block dashboard reads, `save-decisions`, or admin mutations. It is `require_super_admin`, so a facilitator cannot use it, and nothing arms it before a deploy.

**[F] Feature flags are a real asset** — `_god_mode_settings` + per-cohort overrides, shared via the coordination store, snapshotted. **But the Master Variable Editor is non-functional:** `MasterVariableEditor.js:353` sends `PATCH` to an endpoint that defines only `GET`/`PUT` → 405; and even on a `PUT`, `update_god_settings` writes exactly two keys and silently ignores all eight master variables, returning 200 with unchanged settings.

**[F] Rollback:** none described. `restartPolicyMaxRetries: 3` is the only automatic recovery, and it never fires (see the health-check finding). **[I]** A Railway redeploy of a prior image reinstalls the old auto-schema and old `fn_immutable_guard` over data the newer code wrote.

**In-flight state on redeploy:** game state survives (Postgres); pacing/freeze rehydrate; the unlock gate is time-derived and survives. **Lost:** pacing timer tasks (never re-armed), timed-mode straggler auto-commit, and every facilitator note / annotation / bonus / peer evaluation.

**Verdict: Weak.**

---

### K. Onboarding and knowledge risk — **Critical**

**[F] The bus factor is one, literally.** 353 of 366 commits from one email; the remainder are a Railway deployer bot, one `Developer@R-Macs-MacBook-Air.local`, and one Cowork commit.

**Could a competent senior engineer safely change a simulation rule in week one? No.** They would have to know:
- which of the six copies of the M_R formula is authoritative (`terminal_valuation.py:175`) and that the comment 12 lines into the *authoritative R10 function* states the wrong coefficient and the wrong maximum;
- that editing the Excel config parameter for the shadow carbon price changes CAROIC and not the number students see;
- that `_engine_tunables` is a UI that reports success and does nothing for 22 of 24 knobs;
- that `validation_logic.py` (1001 lines) is imported by nothing;
- that `check_auto_pause_triggers` (`admin_router.py:10975`) has zero callers, so the auto-pause feature and its config endpoints are dead;
- that `run_dry_run` has no route, and `DryRunSimulator.js` 404s;
- that adding a field to game state requires hand-adding it to `GlobalStateOut` or players silently lose their allocations;
- that adding an `impacts` key to `round_configs.py` may do nothing depending on the round;
- that the frontend has a hand-mirrored case catalog and reward-function catalog that have already diverged.

**Bus-factor-of-one files:** `admin_router.py` (12.5k lines, 101 commits), `router.py` (7k, 65), `round_logic.py`, `engine.py`. **[F]** The docs are extensive — `SIMULATION_CONTEXT.md` at 58k, `CLAUDE.md`, `blueprint.md`, 12 audit/plan documents — and `CLAUDE.md` in particular is genuinely excellent, precise, and full of *why*. But `README.md:200` tells a newcomer to run two test files that do not exist, and five documents assert CI details that need verifying. **The docs are a strength that is beginning to become a liability**, because a newcomer cannot tell which sentences are still true.

**Verdict: Critical** — and the cheapest partial mitigation is not documentation. It is the golden masters, which turn "does a domain expert understand this?" from a reading problem into an executable one.

---

### L. Configuration and the calibration loop — **Critical**
*(A dimension I did not scope originally. It exists because §9.7 — you retune the model every day, by yourself — turns a set of Medium findings into the thing most likely to be wasting your time right now.)*

Four independent defects compound into one: **you cannot currently trust that a parameter you changed is the parameter the engine used, or that it will still be there tomorrow.**

**1. The knob panel is mostly inert. [F]** `_engine_tunables` (`admin_router.py:10105-10131`) presents 24 values under the banner *"ECONOMIC ENGINE TUNABLES — All 16 engine constants."* `grep -rn "_engine_tunables" backend/` returns **only `admin_router.py`**. The PATCH handler forwards exactly two of them (`admin_router.py:10172-10173`, `overrun_probability` and `overrun_severity`, into `_god_mode_settings`). **The other 22 are write-only.** The endpoint returns `{"changed": {...}}` and the UI reports success. Three of the 24 already disagree with `config.py` by a factor of two — `competitor_growth_rate` 0.03 vs 0.06, `greenwashing_penalty` 8.0 vs 15.0, `vrio_imitation_decay_rate` 0.05 vs 0.10 — so whichever surface you were reading, one of them was lying to you. And because the two live ones are always passed explicitly at `engine.py:2624`, the corresponding `simulation_config.json` values are **dead at runtime**: `_god_mode_settings` wins, and it is a mutable process global the engine reads *mid-tick* (`engine.py:2616-2621`), so toggling a slider changes the model for teams that commit after the toggle and leaves no trace in the run record.

**2. The knob you turn is not always the number the student sees. [F]** `FINANCIAL_SHADOW_CARBON_PRICE` (`config.py:134`) is authorable through the Excel importer (`config_excel.py:48`, described as the internal shadow carbon price). Its only runtime readers are the two CAROIC sites. The **terminal carbon cost** — the one that lands in the Year-5 debrief — comes from `special.get("carbon_tax_per_ton", 250)` at `round_logic.py:2102`, sourced from `round_configs.py:675` / `ending_pathways.py` / `healthcare_configs.py`. Same for the CSF pool: `csf_pool_treasury_fraction` and `csf_pool_floor` are **absent from `simulation_config.json` and from `config_excel.py`'s 194 mapped parameters**, so they are permanently pinned at their Python defaults — while a hardcoded duplicate at `router.py:360` governs auto-committed teams and a third copy at `page.js:392` governs what players are shown.

**3. Hot-reload produces a mixed-config process. [F/I]** `admin_router.py:8767-8792` reloads `config`, `engine`, `balance_sheet`, `terminal_valuation`, `black_swan_registry` and returns `{"reload": "complete", "changes": [...]}` with a full parameter diff. **[I] high confidence:** `round_logic.py:20`, `router.py:23-24`, `npc_stakeholders.py`, `turnaround_engine.py`, `dry_run.py`, `admin_shared.py` and others bind constants with `from config import X` at module scope, which `importlib.reload(config)` cannot rebind; and `router.py:19` holds a direct reference to the *old* `process_tick` function object. So after an upload the process runs a mixture of new and old constants, and reports success. `reload_simulation_config()` (`config.py:640-653`) is dead code with zero callers and would not work either.

**4. Every redeploy discards your work. [F]** The upload writes `simulation_config.json` to the **repo root inside the image**. `runtime_paths.py:24-26` states the exclusion explicitly: *"Deliberately NOT routed through here: seed/config files… Those ship in the image."* Same for `decision_overrides.json`. Your durable volume at `/data` (verified mounted) holds the facilitator registry, cohort settings and the memory snapshot — **not your calibration.** Every `git push` to the deploy branch reverts the tuning to whatever is committed.

**Consequence, stated plainly.** If you have been tuning daily through the UI and the Excel importer, then some unknown fraction of your parameter changes never reached the engine, another fraction reached only half of it, and the ones that did land have been silently reverted on each deploy. **[I]** That also means any calibration judgement you formed by observing output after a change may be built on a change that did not happen — which is a more expensive kind of wrong than a bug, because it corrupts the model's validation rather than its execution.

**The fix is not large**, and it is four separate small things (remediation #22, #29, #37, #38): route config through `runtime_paths.data_dir()`; convert the hot constants from `from config import X` to attribute access (`config.X`) so one reload suffices; wire or delete `_engine_tunables`; and make `round_logic.py:2102` fall back to `FINANCIAL_SHADOW_CARBON_PRICE` so the Excel description is true. **The prerequisite is the financial golden trace (#9)** — otherwise you cannot tell whether the numbers moved because you fixed the plumbing or because you changed the model.

**Verdict: Critical**, on the specific grounds that it is actively taxing the work you do most days.

---

## 5. The bar, and scores against it

### What "extremely well written" means for a *facilitated simulation product*

Your starting position is right and I would extend it in three ways.

> A simulation codebase is excellent when:
> 1. **The model is a first-class, isolated, deterministic, replayable artifact that a domain expert can read.**
> 2. **Every run is fully reconstructable** — decisions, timings, interventions and results — from an append-only record.
> 3. **The system fails loudly and recovers gracefully in a room full of people.**
> 4. **Changing a rule is a small, safe, well-tested diff.**
>
> **Extensions the panel would add:**
> 5. **The configuration a run used is part of the run.** A simulation whose parameters can change under it is not replayable no matter how deterministic the code is. This is the single addition that turns (1) from a property of the code into a property of the *product*.
> 6. **Every number shown to a participant is derived from the same code that scored them.** A second implementation in the UI is not a display concern; it is a pedagogical defect, because the thing students learn is the thing they are shown.
> 7. **The facilitator can see the system's health in the facilitator's own vocabulary.** "Is this run healthy" must be answerable by the person in the room, not only by the person with SSH.

**PA would add an eighth** (*"the transport, the application service and the model are three packages with one-way dependencies"*). **SE objects:** *that's a means, not a bar — a monolith with a clean call graph passes (1)–(7) fine.* **Panel outcome: not adopted as a bar; adopted as the target architecture in §7.**

### Scores

| # | Dimension | Score | Evidence | What a 5 looks like *here* |
|---|---|---|---|---|
| A | Engine correctness & determinism | **1** / 5 | Seed empty by default; 12 unseeded engine sites; two backends give different numbers; R10 re-committable; `random.uniform` in a graded score; no replay | Seed always set and stamped on the run; every stochastic draw through `event_rng`; `replay(session_id)` reproduces stored terminal state bit-for-bit in CI |
| B | Domain modelling & expressiveness | **2** / 5 | Declarative case table (real asset) + 27 imperative modules; 6 live FE/BE rule divergences; a rule unreachable in play | One rules package a modeller can read; every player-visible number served from the engine; a tripwire per mirrored catalog |
| C | State, concurrency, transactions | **2** / 5 | One cross-process lock; no `FOR UPDATE`; 44 unguarded RMW sites; dead optimistic lock; `_fa_force` self-reverting | One `RunStateMachine` owning transitions; `expected_round` required; idempotency keys on every mutating endpoint |
| D | Resilience (run day) | **2** / 5 | Most drill scenarios fail *silent*; connection banner never fires; timer not re-armed; health check can't see the backend | Every drill scenario fails loud, with a facilitator-visible message and a documented recovery action |
| E | Data integrity, audit, recovery | **2** / 5 | Excellent immutability spine; **backups now enabled (§9.4) — the one item that improved**; R10 unlogged; timings fabricated; overrides and undo unaudited; facilitator work product in RAM | Full run reconstruction incl. interventions and timings; every state-changing facilitator action audited; a *rehearsed* restore |
| F | Security & privacy | **1** / 5 | Query-param auth bypass; unauthenticated cohort roster + player ids; plaintext passwords in a list endpoint; ~25 unguarded admin routes; retention reaper dead under Postgres | Player REST auth on a signed token; two guard tripwires green in CI; per-player erasure; retention that runs |
| G | Testing strategy | **2** / 5 | 1,485 tests; one narrow golden master; tautological conservation invariant; 2,661 lines of uncollected "tests"; RNG bleed | Financial golden trace + waterfall conservation + collected full-run HTTP scenario + concurrency + RNG-restore fixture, all gating |
| H | Code quality & craft | **3** / 5 | No bare excepts; excellent *why* comments; 776- and 766-line functions; engine path not on the logger; several load-bearing comments now false | `_commit_turn_impl` under 150 lines; every engine failure structured and surfaced; comments verified by tests where they state numbers |
| I | Observability | **2** / 5 | Genuinely good correlated access log with latency; no metrics, no error tracking; the health chip is hardcoded green | A run-health view a facilitator can read: commits/round, 5xx rate, engine failures, last-poll age per team |
| J | Delivery & change safety | **2** / 5 | Real CI incl. Postgres parity; deploy-during-live unguarded; health check can't detect a dead backend; preflight dead; no rollback path | CI gating with the golden traces; a run-day lock; a health check that fails when the backend fails; documented rollback |
| K | Onboarding & knowledge risk | **1** / 5 | 353/366 commits one author; four bus-factor files; docs drifted; README cites non-existent tests | A second person has shipped a rule change; the golden masters make correctness executable rather than tribal |
| L | **Configuration & the calibration loop** *(added after §9.7)* | **1** / 5 | 22 of 24 tunables inert; carbon-price knob doesn't reach the debrief number; CSF pool unauthorable; hot-reload yields a mixed-config process and reports success; uploads discarded on every redeploy | The parameter you change is the parameter the engine uses, it survives deploy, it is stamped on the run, and the golden trace shows you exactly which numbers your change moved |

**Overall: 1.75 / 5** across twelve dimensions.

**One blunt paragraph.** Muressons is an unusually ambitious product built by one person with real engineering instincts and no safety net, and it is now at the exact point where the instincts stop scaling. The product surface is enormous and largely works; the foundations underneath it are a single unbounded HTTP handler doing the work of four layers, an untyped state bag, two storage backends that disagree about numbers, a determinism story that is off by default, a configuration loop that partly does not connect to the engine and is wiped on every deploy, and a security surface where the *role* dimension was thought through carefully and the *tenant* dimension was not. Nothing here warrants a rewrite — the engine is close to pure, the case table is genuinely readable, the immutability spine is right, backups are now on, and the test *infrastructure* is better than most teams manage. But you are running an instrument that cannot reproduce its own results, in front of paying executives, on a platform whose health check watches the wrong process, while retuning the model daily through knobs that are 22-parts-in-24 inert. **The one genuinely good piece of news is timing: nothing has been graded yet (§9.1), so the determinism work is a window rather than a remediation.** Fix the seven things in "Do before the next live run" in the next five days; then spend a fortnight on the golden masters and the config plumbing; then, and only then, start moving boundaries.

---

## 6. Remediation plan

### 6.0 What your answers changed

| Answer | Effect on the plan |
|---|---|
| **§9.1 Not yet used for grading** | #16 (CEO-interview noise) **High → Medium**. Still fix it — it is four hours — but it is no longer an exposure, it is a window. It also means #9/#14/#15 have a natural deadline: **before the first graded cohort**, not "eventually". |
| **§9.4 Backups enabled** | #20 drops off Do-Now entirely. **Replaced by #20′: rehearse one restore.** An untested backup is a belief, not a control — and this is a fifteen-minute exercise on a staging Railway service. |
| **§9.7 You retune daily, alone** | **The single biggest re-rank.** Dimension L is new and Critical. #22 and #29 move from Structural/Polish into **Foundation**, and three new items (#37, #38, #39) join them. Rationale: this is not a run-day risk, it is a *you*-risk — it silently taxes the work you do most days and corrupts the model validation you are doing it for. |
| **§9.8 Railway is the workshop platform** | The offline-single-laptop justification for the in-memory backend **evaporates**. SE's argument in "Deliberately not doing" loses; that entry is rewritten. New item **#40: run the golden traces under Postgres in CI**, because production is Postgres (verified) and every engine test is memory-mode. |
| **§9.9 20 teams per cohort (20 drivers + read-only observers), multiple concurrent cohorts** | Cross-tenant moves from theoretical to scheduled. New items **#41–#43** (scope the freeze, scope the bell, replace `DISABLE TRIGGER`, move engine params out of `_god_mode_settings`). #33 (capacity) **Med → High**, scoped to the CPU path (20 drivers × 3 ticks) plus a `since_round` client fix; the poll-volume half is conditional on observer device count. New item **#44** — move the barrier off the read path — from a defect found while checking this correction. |
| **§9.10 All engines run** | Confirms all 12 unseeded RNG sites are live → #15 stays High and its acceptance test (Exemplar 3's last case) is not optional. Removes the "delete dormant engines" cheap win I had hoped for in old-Q10. |
| **Production verified: Postgres + durable volume** | #18 (BU ordering parity) **High → Critical-adjacent**: the divergence is live and untested, in the direction production actually runs. `_fa_force` (#13) and the three phantom-write bugs are confirmed-live rather than conditional. Good news: cohort settings and the facilitator registry *are* durable. |
| **Next run in ~5 days, 10 people** | Do-Now is sized for five days, not seven, and the small room means capacity work (#33) is genuinely deferrable — but only until the first 20-team cohort. |

### Ranked table (risk reduction per unit of effort)

| # | Finding | Sev | What breaks if ignored | Fix | Effort | Behaviour risk | Files |
|---|---|---|---|---|---|---|---|
| 1 | `_bypass_password` is a query param | **Critical** | Anyone who learns a player id logs in as them with no password. Reputational + FERPA/GDPR event. | Move to a private impl function; route calls it with `bypass=False` | **15 min** | None | `backend/router.py:810` |
| 2 | Rotate `JWT_SECRET`, `MASTER_PASSWORD`, `PROJECT_ADMIN_PASSWORD` | **Critical** | Secrets left the machine (during this review). `JWT_SECRET` disclosure = mint a god_mode token. | Rotate; restart; invalidate sessions | **15 min** | None | `backend/.env.railway` |
| 3 | `cohort-pulse` unguarded; roster + player ids public | **Critical** | Read/write any team's decisions before reveal | `Depends(require_facilitator)` + `_assert_session_ownership`; strip `player_id` | **30 min** | None | `admin_router.py:11233` |
| 4 | Health check cannot see a dead backend — **verified live** | **Critical** | Crash loop reported healthy; every player 502s; Railway never cycles the container | Delete `frontend/app/api/health/route.js` (the `/api/*` rewrite already proxies), or add a `beforeFiles` rewrite. Verify after deploy: `/api/health` must return `"database":"postgresql"`, not `"service":"frontend"` | **20 min** | None | `frontend/app/api/health/route.js` |
| 5 | Commit retry → double round advance | **Critical** | A team silently plays two rounds on one set of decisions. Corrupts a graded result invisibly. | Send `expected_round` from the client; make it **required** server-side | **1 h** | ⚠️ **Low** — 409s that previously succeeded. Prove with a collected e2e that commits R1→R10. | `useSimulation.js:476`, `router.py:2100`, `models.py:289` |
| 6 | R10 infinitely re-committable | **Critical** | Terminal valuation compounds on re-submit; the graded finale is wrong | Set `game_over` on the normal R10 path; reject commit when set | **1 h** | ⚠️ **Low** — only affects re-commits, which are already wrong | `router.py:2092,2346,2599` |
| 7 | Two RBAC tripwire tests | **High** | ~25 unguarded routes and ~60 missing ownership checks regrow | Test 1: every `@admin_router` route has a `Depends(require_*)`. Test 2: every route with `{session_id}`/`{cohort_id}` calls `_assert_session_ownership`. Allowlist the deliberate exceptions. | **3 h** + fixes | None | new `backend/tests/test_admin_route_guards.py` |
| 8 | `plaintext_password` leaked by `list_players`; `list_sessions` untenanted | **High** | Any facilitator reads every cohort's student credentials | Strip `plaintext_password`; derive `facilitator_id` from the JWT; project through `_roster_view` | **1 h** | None | `admin_router.py:3793`, `:4930` |
| 9 | **Financial golden master** | **High** | Every engine change is unverifiable. This is the safety net everything else needs. | Clone `test_stakeholder_golden_trace.py` onto treasury/EBITDA/tCO2e/synergy/M_R/TV; commit `golden/financial_trace.json`; gate in CI | **1 day** | None (pins current behaviour by definition) | new `backend/tests/test_financial_golden_trace.py` |
| 10 | Treasury waterfall conservation | **High** | A leak in the money path is currently undetectable | Replace the tautological check with the real equation (Exemplar 3) | **3 h** | None | `tests/test_universal_math_engine.py:483` |
| 11 | Engine failures are silent | **High** | A round commits 201 with half its ledgers missing; nobody knows | Convert `round_logic.py`'s 21 `print()` to `logging.getLogger("muressons.engine")`; record `events["engines_failed"]`; surface on the facilitator dashboard | **4 h** | None | `round_logic.py`, `router.py:2481` |
| 12 | Connection banner never fires | **High** | On flaky wifi a player sees a frozen, confident board | Set `connectionState` from the 5s poller's catch block | **30 min** | None | `useSimulation.js:686` |
| 13 | `_fa_force` self-reverting; Force Advance is a no-op under Postgres | **High** | Facilitator presses the button, gets OK, nothing happens | `mark_pacing_dirty(cohort_id)` + add `_fa_*` to `_PACING_LOCAL_FIELDS` | **30 min** | None | `admin_router.py:3404`, `admin_shared.py:1518` |
| 14 | Seed non-empty by default | **High** | Runs are unreproducible from the start | Auto-generate a per-cohort seed at creation; display it; allow override | **2 h** | ⚠️ **Medium** — changes which events fire for cohorts created after the change. Prove with the golden trace + a run of the current suite. | `admin_shared.py:347`, cohort creation |
| 15 | 12 unseeded engine RNG sites | **High** | Reproducibility impossible even with a seed | Convert to `event_rng`; then delete the three `*_enabled: False` lines from the golden trace | **1 day** | ⚠️ **High** — changes outcomes for seeded runs. **Do only after #9.** Prove by rebaselining the golden with a documented diff. | `impact_engine.py`, `org_politics.py`, `board_governance.py`, `supply_chain_network.py`, `regulatory_sandbox.py`, `ending_pathways.py`, `admin_router.py:7227` |
| 16 | CEO-interview noise fallback | **Med** *(was High — §9.1, nothing graded yet)* | 50% of the score is `random.uniform` when the LLM is down. Not yet a grading exposure; **[A]** students may already have been shown random feedback as formative | Return data scores with `llm_used: false` and a visible banner; never score on noise. Pin the model to a dated snapshot; `temperature=0`; cache by `(session_id, hash(responses))` | **4 h** | ⚠️ **Low** — only the no-API-key path, which is already wrong | `router.py:5775`, `ceo_interview.py:648-672` |
| 17 | R10 writes no audit rows | **High** | The graded finale has no decision record | Call `db.log_decisions(...)` in the R10 branch | **1 h** | None | `router.py:2606` |
| 18 | BU ordering parity + `int()` truncation | **High → do it in Step 2, first** | Same seed → different numbers on Postgres vs memory. **Production is Postgres (verified); every engine test is memory-mode — so the micro-strike hits a different BU in production than in any test you have run.** | Order both backends by canonical `DEFAULT_SLOTS`; target the micro-strike by `bu_id`, not index; drop the `int()` | **3 h** | ⚠️ **Medium** — changes which BU is struck. Prove with a Postgres-vs-memory **value**-parity test (the existing tripwire is signatures only). | `database.py:889`, `database_memory.py:784,802`, `engine.py:2515` |
| 19 | Audit the six graded-outcome actions | **High** | Overrides, undo and force-advance leave no record; a grade appeal is undefendable | `_audit()` on `apply_override`, `undo_round`, `force_advance_cohort`, `set_pacing`, `unlock/relock`, `delete_session` | **3 h** | None | `admin_router.py` |
| 20′ | **Rehearse** the restore *(backups themselves are done — §9.4)* | Med | An untested backup is a belief, not a control. You have already lost a database once; the second time you want the procedure to be muscle memory, not discovery. | Restore last night's snapshot onto a throwaway Railway service, boot the app against it, confirm a cohort's round history is intact. Write down the steps and the elapsed time. | **1 h** | None | ops |
| 21 | `set-username` unauthenticated; quiz answer key public; `change-password` unrate-limited | High | Facilitator username hijack; graded quiz trivially passed; password oracle | Guards + rate limits | **2 h** | None | `router.py:541,4452,4245` |
| 22 | CSF pool: 3 copies, unauthorable | **High — Foundation** *(§9.7)* | Teams scored on different pools; the knob you would reach for does not exist | Add both keys to `simulation_config.json` + `config_excel.py`; use the constants at `router.py:360`; **serve the pool from the server** and delete the client formula | **4 h** | ⚠️ **Low** — only if a config value differs from 0.20/5M | `config.py:143`, `router.py:360`, `page.js:389` |
| 23 | Server-side R1/R2 gates | High | The two mandatory pedagogical gates are browser-only | Add both next to the existing quiz gate | **2 h** | ⚠️ **Low** — will start rejecting commits that previously passed. Announce it. | `router.py:2146` |
| 24 | `update_session_metadata` lost writes | Med | Roster mints, consent and pace locks race and lose | `conn.transaction()` + `SELECT … FOR UPDATE` | **2 h** | None | `database.py:362` |
| 25 | Undo/reset take no lock; `DISABLE TRIGGER` blocks the platform | Med | Undo racing a commit corrupts the chain; every cohort stalls | Take the advisory lock; use `SET session_replication_role = replica`; make cohort reset one transaction | **1 day** | None | `database.py:1349,1607`, `admin_router.py:9019` |
| 26 | Retention reaper dead under Postgres | Med | Student PII retained indefinitely against a configured policy | Lift the `_memory_backend_active()` guard off the retention branch; add a per-player erasure endpoint | **4 h** | None | `session_reaper.py:99` |
| 27 | Config versioning: stamp the run | Med | Last term's run can never be re-derived | Hash `SIMULATION_CONFIG` + `round_configs` + effective cohort settings into `sessions.metadata` at creation | **4 h** | None (additive) | `database.py:520` |
| 28 | Persist facilitator work product | Med | Notes, annotations, bonuses, peer evals lost every restart | Move to the store; snapshot them | **1 day** | None | `admin_router.py:9050,9143,9219,11063` |
| 29 | `_engine_tunables` | Med | A super-admin UI that lies | Delete it, or wire all 24 to config | **4 h** | ⚠️ **Low** if wired (2 currently-live knobs move ownership) | `admin_router.py:10105` |
| 30 | Six frontend/backend rule divergences | Med | Students taught a reward function the engine doesn't implement | Serve M_R breakdown + case catalog from the API; delete the client copies; add tripwires for what remains | **2 days** | None (display only) | `mrJourney.js`, `SustainabilityBalancedScorecard.js:2027`, `TechnicalGlossary.js` |
| 31 | Collected full-run HTTP test | Med | No test plays a whole game over HTTP | Port `test_e2e_full_flow.py` into `backend/tests/` with real asserts | **1 day** | None | new |
| 32 | RNG-restore autouse fixture | Med | The engine suite is order-dependent; green ≠ green | Snapshot/restore `random.getstate()` per test | **1 h** | None | `backend/tests/conftest.py` |
| 33 | Capacity at 20 drivers (§9.9, corrected) | **High** *(was Med)* | **~60 serial synchronous ticks** in the closing seconds of a round — 20 commits × 3 (`process_tick` + two decision-regret shadow ticks) — on a single event loop. This half is independent of observer count. Poll volume is 160–960 q/s depending on devices. **Deferrable only until the first 20-team cohort.** | `run_in_executor` for `process_tick`; **make decision-regret opt-in — it is the cheapest 3× win available**; send `?since_round=` from the client; compute `_cohort_advance_status` once per cohort per poll window instead of once per caller | **2 days** | ⚠️ **None** if the tick itself is unchanged — verify with the golden trace | `router.py:2333,2740,304,450`, `useSimulation.js:689` |
| 34 | **The four unreachable modules — see §8.1 for the phased plan** | Mixed | `deploy_preflight` never warns; `scale_preflight` is invisible to static analysis and one sweep from deletion; `market_dynamics` is a live toggle wired to nothing; `dry_run` 404s on click **and would rewind every live cohort's RNG if wired as-is** | **Phase A (Do-Now, ~2.5 h):** wire `deploy_preflight`; add an entrypoint tripwire for `scale_preflight`; disable the `market_dynamics` toggle; hide the `DryRunSimulator` tab. **Phase B (Step 1.5):** fix `dry_run`'s global reseed + `hash()`, add the route, offload it. **Phase C (gated on #44 + Step 2):** decide on `market_dynamics` | **A: 2.5 h · B: 1 day · C: 1 wk + decision** | A: None · B: ⚠️ Low once #15 lands, **High if wired before** · C: ⚠️ High | §8.1 |
| 35 | Dead code — **now enumerated by import-graph analysis, see §9.10** | Low | Onboarding tax; false confidence | **Delete outright:** `validation_logic.py` (1001), `stakeholder_bulk_excel.py` (448). **Wire or delete:** `dry_run.py` + `DryRunSimulator.js` (328, currently 404s on click), `deploy_preflight.py` (186, see #34). **Dead functions in live modules:** `check_auto_pause_triggers`, `reload_simulation_config`, `_decode_token_ignore_expiry`, `_async_write_lock`, the EU AI Act rule at `round_logic.py:1834`. A `vulture` pass would likely find more | **1 day** | None | see §9.10 |
| 45 | **`market_dynamics.py` is dormant behind a live facilitator toggle** *(found answering your §9.10 question)* | Med | A facilitator ticks "Market Dynamics" — tooltip promises a shared carbon-credit pool, competitive talent hiring and scarcity pricing — and **nothing happens**. Fifth instance of the Dimension L pattern. | Wire the module, or remove the toggle from `CreateCohortModal.js:77` and `GodModeStatus.js:391` and strip the setting. Do not leave it as-is. See §8.1 Phase A/C. | **1 h** (unadvertise) / **1 wk** (wire) | ⚠️ **High if wired** — new cross-player coupling. Do it after #9 and #44, never before. | `market_dynamics.py`, `admin_router.py:521,609`, `CreateCohortModal.js:77`, `GodModeStatus.js:391` |
| 46 | **Per-cohort cache for the commit-progress scan** *(§9.9 — observers use their own laptops)* | **High** | ~550 queries/second at 20 teams × 6 laptops, to render one badge. 120 clients each run the identical 20-sibling scan every 5 seconds. | Compute `(committed, teams)` **once per cohort** behind a 2–3 s TTL cache and serve every poller from it; recompute eagerly on commit. Also fix the stale *"capped at 5 players"* docstring. This is the single cheapest capacity win available — roughly an 80× reduction in read volume for ~30 lines. | **4 h** | None — same values, computed once instead of 120 times | `router.py:283-315,1901` |
| 47 | **No way to see what config the engine is actually running** *(§9.7 + §10.4 — you use all three tuning paths)* | **High** | With three tuning surfaces that each fail differently and can silently disagree, there is no way to answer "did my change take?" except by watching outputs — which is exactly the observation determinism has already made unreliable. | `GET /api/admin/config/live` returning the **in-memory** value of every engine constant that matters, each tagged with its resolved source (`simulation_config.json` / hardcoded default / `_god_mode_settings` override / stale import binding), plus a fingerprint hash. Render it next to the upload button and stamp the hash on each run (#27). Then a knob that didn't take is *visible*, not inferred. | **1 day** | None (read-only) | new `backend/config_introspect.py`, `admin_router.py` |
| 36 | Comment truth pass | Low | The most-trusted comments state wrong numbers | Fix `round_logic.py:2116`, `engine.py:632`, `router.py:291,842`, `docker-start.sh:65` | **2 h** | None | various |
| **New — added after your answers** | | | | | | | |
| 37 | Config uploads are discarded on every redeploy | **High** | **Your daily tuning is reverted by every `git push`** (§9.7) | Route `simulation_config.json` and `decision_overrides.json` through `runtime_paths.data_dir()` (your `/data` volume is verified mounted and writable); migrate the committed file in on first boot if absent | **3 h** | None | `runtime_paths.py:24`, `admin_router.py:8615` |
| 38 | Hot-reload leaves a mixed-config process, reports success | **High** | You cannot tell which constants the engine is running after an upload | Convert `from config import X` to `config.X` attribute access in the ~10 modules that bind constants at import; re-resolve `process_tick` through the module. Then a single `importlib.reload(config)` is sufficient and honest | **1 day** | ⚠️ **Low** — makes previously-ignored config values take effect. **Run the golden trace before and after; any diff is a value that was silently inert.** | `config.py`, `round_logic.py:20`, `router.py:19,23-24`, `admin_router.py:8767` |
| 39 | Terminal carbon price ignores the config knob | High | Editing the Excel parameter changes CAROIC, not the number in the Year-5 debrief | `round_logic.py:2102` → fall back to `FINANCIAL_SHADOW_CARBON_PRICE` instead of the literal `250` | **1 h** | ⚠️ **Low** — only if the configured value ≠ 250 | `round_logic.py:2102`, `config.py:134` |
| 40 | Golden traces run on a backend production doesn't use | **High** | The suite validates a BU ordering and a `tco2e` type that production does not have (§2.8) | Parameterise the golden traces over both backends; run them in the existing `backend-postgres` CI job | **4 h** | None | `.github/workflows/ci.yml`, `tests/golden/` |
| 41 | Freeze, bell and god-mode engine knobs are platform-global | **High** *(§9.9, concurrent cohorts)* | One facilitator's action hits every other live classroom — including engine parameters read mid-tick | Key `system_frozen` by cohort; scope `broadcast_students` to a cohort; move `overrun_probability`/`overrun_severity`/`global_carbon_fee`/`market_hostility_index` out of `_god_mode_settings` into per-run persisted config | **2 days** | ⚠️ **Low** — the engine params become per-run rather than ambient; pin with the golden trace | `admin_shared.py:292,312`, `admin_ws.py:96`, `engine.py:2616`, `admin_router.py:9821` |
| 42 | `DISABLE TRIGGER` stalls every concurrent cohort | Med | An undo in cohort A blocks commits in cohorts B and C for its duration | `SET session_replication_role = replica` (session-scoped, no table lock) instead of `ALTER TABLE … DISABLE TRIGGER`; make cohort reset one transaction | **1 day** | None | `database.py:1367,1607,1475` |
| 43 | Capture a real run as a golden fixture | Med | §9.6 — you have no recorded run, so the golden master must be synthetic | Persist the **full** commit envelope (`dividends_paid`, `pillar_decisions`, `emergency_credit_used`, `engagement_action`, `force_override_cfo`, `investment_ratio`) into `decision_audit_log.metadata`, then export the next real cohort as a replay fixture | **4 h** + one run | None (additive) | `database.py:1148`, `router.py:2571` |
| 44 | **The round barrier is enforced on the read path** *(found while checking §9.9)* | **High** | A GET has a side effect that commits a *different* team's round — and an observer's browser can be the trigger. Symmetrically, if nobody polls, Force Advance and the round timeout **never fire**. Both halves are the same defect: `get_dashboard` is the scheduler. | Move `_auto_commit_laggards` out of `_cohort_advance_status` into a single cohort-scoped background task owned by `RunService` (Step 4). Interim, if that is too big before the next run: keep the read-path trigger but **gate it to driver callers** (`allow_observer` is already threaded through `_assert_player_owns_session` — pass the flag down), so a spectator cannot commit for anyone. | **1 day** (interim: **1 h**) | ⚠️ **Low** — changes *who* triggers auto-commit and *when*, not what it computes. Pin with a test that a cohort advances on time with **zero** dashboard polls. | `router.py:485-512,1901-1910`, `admin_router.py:3272` |

### 6.05 The two dates you just gave me change the shape of everything

**Next run: ~5 days, 10 people. First graded AND first 20-team cohort: 2 weeks, single cohort.** And **yes to a second engineer.** Three consequences, in order of size:

1. **You now have a hard 14-day deadline on the determinism work.** "Before the first graded cohort" stopped being a date you control. Step 1 (golden traces) + the determinism half of Step 2 must land inside two weeks, or that cohort is graded on results the system cannot reproduce. That is achievable — see §6.1 — but only if the config work (Step 1.5) slips past it, which is fine because the JSON-and-redeploy path works.
2. **#16 goes back to High.** I downgraded the CEO-interview noise fallback to Medium on "nothing graded yet." That answer just changed. In 14 days, 50% of a competency score falling back to `random.uniform(-1, 1)` when the LLM is unreachable becomes a grading defect. It is four hours. Do it.
3. **Single cohort is a genuine reprieve — #41 and #42 come off the critical path entirely.** The global freeze, the platform-wide bell and the `ACCESS EXCLUSIVE` undo lock are only incidents when two rooms run at once. Schedule them, don't rush them. **But #46 and #33 move onto the critical path**, because 20 teams × 6 laptops ≈ 120 pollers arrives in 14 days, and `MAX_PLAYERS_CEILING = 20` is by its own docstring the untested edge.
4. **A second engineer changes the Structural block.** Step 5 (splitting the routers) goes from "drop it entirely" to **worth scheduling** — a 12,492-line file with 232 endpoints is precisely what makes a new hire slow and dangerous. #7 (the two RBAC guard tripwires) rises with it, because they are what makes that split *safe* rather than a game of spot-the-missing-`Depends`. And Dimension K stops being a note and becomes a plan: **their first-week task should be #35 + #45** (the dead-code and dormant-toggle cleanup) — small, isolated, no behaviour risk, and it forces them to read the import graph, `CLAUDE.md` and the tripwire suite, which is the fastest honest tour of this codebase.

### 6.1 The 14-day plan to a graded, 20-team run

One engineer, ~10 working days, with the second engineer arriving on the side track. Ordered so that nothing is ever un-netted.

| Days | Work | Why here |
|---|---|---|
| **1** | **Re-apply the `f3f5956` pacing fix; go green on `test_pacing_gated_modes.py`.** Then #1–#6, #12, #13, §8.1 Phase A. Rotate the three secrets. | Everything that can fail in front of the ten-person room in five days. Finding 1 is already done. |
| **1 (½ day)** | **#20′ rehearse the restore.** | You have backups and have never used them. Fifteen minutes now, or an hour of discovery on a bad day. |
| **2–4** | **#9 financial golden trace + #10 treasury conservation.** Gate both in CI. | The net. Nothing after this line is safe without it, and #9 doubles as your daily "did my tuning move anything?" instrument. |
| **4** | **#32 RNG-restore fixture + #40 goldens under Postgres.** | Without #32 a green suite is not evidence the next run is green. Without #40 you are pinning a BU ordering production does not use. |
| **5–7** | **#18 BU-ordering parity, then #14 seed always set, then #15 the twelve RNG sites.** Rebaseline the golden once, review the diff deliberately. | The determinism block, in dependency order. #18 first because production is Postgres and every test is memory-mode. |
| **7** | **#16 CEO-interview** (no noise fallback, pin the model, `temperature=0`, cache). | It is graded in a week. |
| **8** | **#17 R10 audit rows + #19 audit the six graded-outcome actions.** | A graded run you cannot reconstruct is a grade you cannot defend. R10 is the round the grade comes from. |
| **9–10** | **#46 per-cohort cache, #33 capacity** (offload `process_tick`, decision-regret opt-in, `?since_round=`), **#44 interim** (gate the barrier to driver callers). Then **rehearse the load** with the k6 harness in `load_tests/` at 20 teams × 6. | 120 pollers and ~60 serial ticks arrive on day 14. Rehearse it on day 10, not on the day. |
| **Side track** | Second engineer: **#7 guard tripwires**, then **#35 + #45** dead-code and the dormant `market_dynamics` toggle. | Isolated, zero behaviour risk, and it is the fastest way to learn this codebase honestly. |

**Deliberately NOT in the 14 days:** Step 1.5 (the config plumbing — keep using JSON-and-redeploy), #41/#42 (single cohort, so not yet an incident), Step 3+ (the architecture work), `market_dynamics` wiring, `dry_run` wiring. **If you slip, slip the capacity work (days 9–10) and cap the first graded cohort at 10 teams — do not slip the determinism block.** A slow run you can explain beats a fast one you cannot.

### Do before the next live run — **~5 days, per your comment**
**#1–#6, #12, #13, plus §8.1 Phase A (#34)** — roughly one focused day plus a couple of hours. Every one is either a security event, something that can fail visibly in front of the cohort, or a control that currently lies to the operator; none carries meaningful behaviour risk. **#20′ (rehearse the restore)** is a good use of a spare hour in the same week now that backups exist. Everything else can wait for the block below.

Sanity check after deploying #4: `curl https://cso.mastersustainability.org/api/health` should return `"database":"postgresql"`, not `"service":"frontend"`.

### Foundation
**#9, #10, #7, #11, #17, #19, #31, #32** — the safety nets — **plus the configuration cluster #37, #38, #39, #22, #29, #40**, which §9.7 promoted into this block. **#9 (the financial golden master) remains the single highest-value item in this review**: it is a prerequisite for #14, #15 and #18, *and* it is the only way to tell whether fixing the config plumbing changed the model or merely revealed what you had already set. Do #9 before #38, not after.

> **Hard constraint, stated explicitly because you asked me not to let you infer it:**
> **Do not touch the engine, `round_logic`, the balance sheet or terminal valuation until #9 and #10 are green and committed.** Not the RNG conversion, not the BU ordering, not a refactor, not a "harmless" extraction. The golden trace + the conservation equation are the characterization tests; without them, every subsequent recommendation in this review is a guess dressed as a plan. Build the net first.

### Structural
**#14, #15, #18, #23, #24, #25, #26, #27, #28, #41, #42, #43** and then the architecture work in §8. Each carries a labelled behaviour risk and each is gated on the Foundation block. **#33 and #41 become urgent the moment you schedule a 20-team cohort or two concurrent cohorts** — not before, but bring them forward the day that appears in the calendar rather than the week of.

### Polish
**#16, #30, #34, #35, #36, #45.** (#45 — the dormant `market_dynamics` toggle — is Polish only in the *unadvertise* form, which is an hour. Actually wiring the engine is Structural at best and carries high behaviour risk; do not attempt it before the golden traces exist.)

### Reconsider before the first 20-team or concurrent-cohort run
**#33, #41, #42, #44.** None of these matter at ten people in a room. All four become first-order the day you schedule a full cohort or two rooms at once — and #44 is the cheapest of them in its interim form (one hour to stop observers triggering other teams' auto-commits).

### Deliberately not doing

- **A rewrite.** The engine is close to pure, the case table is readable, the immutability spine is right, and the test infrastructure is better than most teams manage. Everything wrong here is reachable incrementally. Arguing the other side honestly: a rewrite would let you build the model as a versioned, replayable package from day one — but it would cost 6–12 person-months you do not have, throw away 366 commits of calibration you *cannot re-derive* (there is no replay to check a rewrite against), and land you in the same place with less validated content. **Incremental wins decisively.**
- **`Decimal` for money.** SMP argued for it on auditability; PA and SE overruled on churn. Deterministic IEEE-754 on a pinned CPython replays fine, the golden trace already rounds to 4 dp, and 400+ `round()` sites is a large diff with a large behaviour risk for a benefit you get more cheaply from the conservation assertion (#10). **Revisit only if you ever need to reconcile to the cent.**
- **Splitting `admin_router.py` wholesale.** PA wanted this and lost. 232 endpoints with ~30 ownership checks and no route-guard tripwire is a file where a move-only refactor will drop a `Depends`. Do #7 first (the tripwires make the split *safe*), then extract the **catalogs** (`_scenario_presets`, `SWIPE_FILE_PRESETS`, `_SHOCKWAVE_EVENTS`, `_MOD4_CHOICE_IMPACTS`) into data modules, which is the highest-value 10% of the split. The other 90% can wait indefinitely.
- ~~**Deleting the in-memory backend.**~~ **Reversed by §9.8.** I originally kept it on SE's argument that it was your offline-single-laptop workshop story. You have told me the Railway deployment *is* the workshop platform, which removes the only operational justification. PA and SMP now carry it: a second implementation that returns business units in a different order, truncates emissions to `int`, and aliases `get_session_info` to a live store reference is not a fallback — it is a second product, and it is the one all 1,485 of your tests actually exercise. **Revised recommendation: demote it to a test/dev fixture.** Concretely — (a) do #40 so the golden traces run under Postgres, (b) do #18 so the divergences close, (c) keep the module and the AST tripwire (it costs nothing and `USE_MEMORY_DB=true` is a genuinely useful dev affordance), but (d) stop treating memory-mode green as evidence about production. This is a *posture* change, not a deletion — deleting 1,443 lines that 126 test files depend on would be churn.
- **Redis / a message queue / a real event bus.** At one worker, 20 players and a 5-second poll, the coordination store over Postgres `LISTEN/NOTIFY` is correct and adequate. Adding infrastructure would add a run-day failure mode you cannot debug in the room. Revisit when `WEB_CONCURRENCY > 1` is genuinely needed.
- **TypeScript on the frontend.** 86k lines, one author, and the type-safety problem that actually costs you is on the *backend* (`round_logic.py` at 78% untyped), not in React. If you want types, spend them on the rules core.
- **Alembic.** Single writer, additive schema, `CREATE TABLE IF NOT EXISTS` + one `ADD COLUMN IF NOT EXISTS`. Adding a migration framework now is ceremony. **But add the tripwire test that pins `db/init.sql` equal to the auto-schema in `database.py`** — you have that pattern three times already for lesser things.
- **Fixing the 23 regex-over-source frontend tests.** They are implementation-coupled and brittle, and rewriting them as behavioural tests is a week of work that finds no bugs. Freeze them, stop writing new ones, and let them decay.
- **`_commit_turn_impl` decomposition as a standalone task.** It falls out of the target architecture (§8, Step 3). Doing it as a pure refactor first is churn with no safety net.

---

## 7. Three worked exemplars

### Exemplar 1 — The API signature *is* the security boundary

**Principle.** In a declarative framework, the function signature is not an implementation detail — it is the public contract. FastAPI binds every non-path, non-Pydantic scalar parameter with a default as a **query parameter**, and a leading underscore does not make it private. A comment asserting a safety property is worth exactly nothing next to a signature that contradicts it. Any parameter that changes an authorization decision must be structurally unreachable from the wire, not conventionally unreachable.

**Current code** — `backend/router.py:810-845`:

```python
@router.post("/public/sessions/{session_id}/join", summary="Join an active session")
async def join_session(session_id: str, req: JoinSessionRequest, _bypass_password: bool = False):
    ...
        if player_record and player_record.get("password") and not _bypass_password:
            # _bypass_password is set ONLY by player_login after it has already
            # verified a team view code against team_view_password — never from
            # an HTTP body, so it cannot be used to skip a driver's password.
            master_ok = verify_player_master_password(req.password)
            if not master_ok and not _verify_pw(req.password, player_record["password"]):
                raise HTTPException(status_code=403, detail="Incorrect password.")
```

**Reproduced** (FastAPI 0.141.1, minimal repro of the same signature shape):

```
POST /join/abc                          -> {"bypass": false}
POST /join/abc?_bypass_password=true    -> {"bypass": true}
```

So `POST /api/simulations/public/sessions/{cohort_id}/join?_bypass_password=true` with `{"player_id": "MUR-004", "password": ""}` skips bcrypt entirely. The only remaining gate is `validate_player_id`, which checks *membership*, not *authentication* — and player ids are published unauthenticated by `cohort-pulse`.

**Before you change it, know what legitimately uses it. [F]** `router.py:767`, inside `player_login`, calls `join_session(cohort_session_id, join_req, _bypass_password=_as_observer)` **after** verifying the presented view code against the team's stored `team_view_password` hash (`router.py:748-750`). That is the real, correct use: an observer has already authenticated with the team's view credential, so re-checking the *driver's* password would be wrong. **The fix must keep that path working — deleting the parameter outright breaks every observer seat.** Make it unreachable from the wire, not non-existent.

**Refactored:**

```python
async def _join_session_impl(
    session_id: str,
    req: JoinSessionRequest,
    *,
    bypass_password: bool,          # keyword-only, never bound by FastAPI
) -> dict:
    """Internal join. `bypass_password=True` is reachable ONLY from
    player_login, after it has verified a team view code."""
    is_valid = await db.validate_player_id(session_id, req.player_id)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Invalid Player ID for this session.")
    ...
    if player_record and player_record.get("password") and not bypass_password:
        master_ok = verify_player_master_password(req.password)
        if not master_ok and not _verify_pw(req.password, player_record["password"]):
            raise HTTPException(status_code=403, detail="Incorrect password.")
    ...


@router.post("/public/sessions/{session_id}/join", summary="Join an active session")
async def join_session(session_id: str, req: JoinSessionRequest) -> dict:
    # No third parameter exists on the wire. The bypass is not expressible.
    return await _join_session_impl(session_id, req, bypass_password=False)
```

Update the one internal caller in `player_login` to `await _join_session_impl(sid, req, bypass_password=True)`.

**The test that pins it** — `backend/tests/test_join_password_enforced.py`:

```python
import pytest
from fastapi.testclient import TestClient

BYPASS_SPELLINGS = [
    "_bypass_password=true", "_bypass_password=1", "_bypass_password=True",
    "bypass_password=true", "_bypass_password=yes",
]

def test_observer_login_still_works_after_the_fix(client: TestClient, seeded_cohort_with_view_code):
    """The bypass has ONE legitimate caller — player_login, for an observer who
    has already presented a valid team view code (router.py:748-767). Locking
    the parameter must not break the observer seat. This test is the reason to
    make the bypass keyword-only rather than deleting it."""
    cohort_id, view_code, view_password = seeded_cohort_with_view_code
    r = client.post("/api/simulations/player-login",
                    json={"player_id": view_code, "password": view_password})
    assert r.status_code == 200
    assert r.json()["is_observer"] is True


@pytest.mark.parametrize("qs", BYPASS_SPELLINGS)
def test_join_never_accepts_a_password_bypass_from_the_wire(client: TestClient, seeded_cohort, qs):
    """SEC: no query string may skip the bcrypt check on join.

    Regression for the 2026-08 finding: `_bypass_password: bool = False` in the
    route signature was bound by FastAPI as a QUERY parameter, making the
    password check skippable by anyone who knew a player id."""
    cohort_id, player_id = seeded_cohort
    r = client.post(
        f"/api/simulations/public/sessions/{cohort_id}/join?{qs}",
        json={"player_id": player_id, "password": "definitely-wrong"},
    )
    assert r.status_code == 403, f"password bypassed via `?{qs}` -> {r.status_code}"


def test_join_route_exposes_no_scalar_query_parameters(client: TestClient):
    """Structural guard: the join route's OpenAPI schema must declare exactly
    one parameter (the path id). Any new scalar with a default is a query
    parameter and therefore part of the public contract."""
    schema = client.app.openapi()
    params = schema["paths"]["/api/simulations/public/sessions/{session_id}/join"]["post"].get("parameters", [])
    assert [p["name"] for p in params] == ["session_id"]
```

The second test is the one that matters long-term — it generalises the lesson to every future parameter on that route.

---

### Exemplar 2 — Idempotency belongs at the boundary, not in the lock

**Principle.** Locks make concurrent duplicates safe. They do nothing about *sequential* duplicates — a retry after a lost response, a phone waking up, a proxy timing out. On flaky venue wifi, sequential duplicates are the *common* case. The fix is not a longer cooldown; it is making the request state what it believes the world looks like, so the server can reject a request built on a stale view. Note the shape of this bug: **the guard was written, and the client was never taught to send it.** A guard with no caller is worse than no guard, because it reads as covered.

**Current code.** Server (`backend/router.py:2099-2109`):

```python
    # ── ITEM 1: Optimistic locking — expected_round guard ────
    expected_round = getattr(body, 'expected_round', None)
    if expected_round is not None and expected_round != current_round:
        if commit_lock.locked(): commit_lock.release()
        raise HTTPException(status_code=409, detail=f"Stale round: expected {expected_round} …")
```

`models.py:289` declares it `Optional[int] = None`. `grep -rn "expected_round" frontend/` → **zero hits.** The guard has never fired in production.

Client (`frontend/app/hooks/useSimulation.js:476-487`):

```js
if (res.status === 429) {
    const retryCount = payload._retryCount || 0;
    if (retryCount < 2) {
        commitInProgressRef.current = false;
        setLoading(false);
        await new Promise(r => setTimeout(r, 5200));
        return commitTurn({ ...payload, _retryCount: retryCount + 1 });  // same payload, later round
    }
```

**The failure, concretely.** Team commits R7. The response is lost (proxy timeout). Client retries → 429 from the 5s cooldown → sleeps 5.2s → retries → cooldown expired, lock free, `fetch_latest_state` now returns round **8** → **the same R7 decisions commit round 8.** `uq_session_round` does not fire; the round numbers differ. The team has silently played two rounds on one set of decisions, and nothing in the system knows.

**Refactored.** Server — make it required, not optional:

```python
# models.py
class CommitTurnRequest(BaseModel):
    expected_round: int = Field(
        ...,                                   # REQUIRED. A commit must state the
        ge=1, le=10,                           # round it believes it is committing.
        description="The round the client believes is current. A mismatch is a stale "
                    "client view (lost response, retry, sleeping laptop) and is rejected.",
    )
    ...

# router.py — inside _commit_turn_impl, immediately after fetch_latest_state
    if body.expected_round != current_round:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "stale_round",
                "expected": body.expected_round,
                "current": current_round,
                "message": (
                    f"This round has already been committed (you are on round {current_round}). "
                    "Your decisions were saved — nothing was lost."
                ),
            },
        )
```

Client — send it, and treat 409 as *success*, because it is:

```js
const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...playerIdHeader() },
    body: JSON.stringify({ ...payload, expected_round: roundNumber }),
});

// 409 stale_round means an EARLIER attempt of ours already landed.
// Re-sync rather than reporting a failure the player cannot act on.
if (res.status === 409) {
    const body = await res.json().catch(() => ({}));
    if (body?.detail?.code === 'stale_round') {
        await fetchDashboard({ force: true });
        return null;                     // not an error path
    }
}
```

And close the R10 hole the same way — set `game_over` on the normal finale path (`router.py:2599`) and reject a commit when it is set, so R10 stops being the one round with no uniqueness constraint behind it.

**The test that pins it** — `backend/tests/test_commit_idempotency.py`:

```python
@pytest.mark.asyncio
async def test_retry_after_lost_response_cannot_advance_a_second_round(app_client, team_session):
    """A retry of a commit whose RESPONSE was lost must 409, not silently
    advance. Regression for the 2026-08 double-advance: the client retried a
    429'd commit after the cooldown, by which time the round had moved on, and
    the SAME decisions committed the NEXT round."""
    sid = team_session
    payload = decisions_for(round=1)

    r1 = await app_client.post(f"/api/simulations/{sid}/commit-turn",
                               json={**payload, "expected_round": 1})
    assert r1.status_code == 201
    assert r1.json()["new_round_number"] == 2

    # Simulate the client's retry: same payload, same expected_round, after the
    # 5s cooldown has lapsed (patched, not slept).
    _commit_timestamps.pop(sid, None)
    r2 = await app_client.post(f"/api/simulations/{sid}/commit-turn",
                               json={**payload, "expected_round": 1})

    assert r2.status_code == 409
    assert r2.json()["detail"]["code"] == "stale_round"

    state = await db.fetch_latest_state(sid)
    assert state["global_state"]["round_number"] == 2, "the retry advanced a second round"


@pytest.mark.asyncio
async def test_round_10_cannot_be_committed_twice(app_client, team_at_round_10):
    """R10 persists in place and has no uq_session_round to violate. A second
    commit must be refused by the game_over guard, not silently re-run the
    engine over already-resolved terminal state."""
    sid = team_at_round_10
    first = await app_client.post(f"/api/simulations/{sid}/commit-turn",
                                  json={**decisions_for(round=10), "expected_round": 10})
    assert first.status_code == 201
    tv1 = (await db.fetch_latest_state(sid))["global_state"]["terminal_valuation"]

    _commit_timestamps.pop(sid, None)
    second = await app_client.post(f"/api/simulations/{sid}/commit-turn",
                                   json={**decisions_for(round=10), "expected_round": 10})
    assert second.status_code == 409

    tv2 = (await db.fetch_latest_state(sid))["global_state"]["terminal_valuation"]
    assert tv1 == tv2, "re-commit mutated the terminal valuation"


@pytest.mark.asyncio
async def test_every_mutating_player_route_declares_expected_round(app_client):
    """Structural: a new commit-shaped endpoint must not ship without the guard."""
    schema = app_client.app.openapi()
    for path, ops in schema["paths"].items():
        if path.endswith("/commit-turn") or path.endswith("/commit"):
            body = ops["post"]["requestBody"]["content"]["application/json"]["schema"]
            required = resolve_ref(schema, body).get("required", [])
            assert "expected_round" in required, f"{path} has no stale-round guard"
```

---

### Exemplar 3 — Pin behaviour before you touch it, and make the invariant reachable

**Principle.** A characterization test does not assert that the code is *correct*. It asserts that the code is *the same*, which is the only property that lets you refactor a validated model safely. Two things make one worth having: it must cover the numbers people are graded on, and its failure must be *unambiguous* — one committed fixture, byte-compared, with an explicit rebaseline ritual so that changing it is a deliberate act recorded in a diff. And an invariant that cannot fail is worse than no invariant: it occupies the slot where a real check would go, and it reads green forever.

**Current code.** The tautology — `backend/tests/test_universal_math_engine.py:357` and `:483`:

```python
        ledgers.append(RoundLedger(
            treasury_start=treasury_before,
            treasury_end=new_gs["corporate_treasury"],
            csf=csf, total_capex=total_capex, loan_interest=loan_int, ...))
        gs = new_gs                # round N+1's treasury_start IS round N's treasury_end
...
def check_invariant_1_treasury_conservation(ledgers):
    for ledger, next_ledger in zip(ledgers, ledgers[1:]):
        if abs(ledger.treasury_end - next_ledger.treasury_start) > 0.01:   # unreachable
            report_violation(...)
```

Every term of the real waterfall is recorded. None is used. And `balance_sheet.py:840-846` does the same thing one layer down:

```python
    bs["retained_earnings"] = round(bs["net_assets"] - fixed_equity, 2)   # a plug
    total_equity = round(bs["net_assets"], 2)
    diagnostics["balance_sheet_balanced"] = True    # cannot be False
    diagnostics["imbalance"]              = 0.0     # cannot be non-zero
```

**Refactored — the invariant that can actually fail:**

```python
def check_invariant_1_treasury_conservation(ledgers, tol: float = 0.01) -> None:
    """Treasury moves ONLY through the documented waterfall.

    Every term below is already recorded by RoundLedger. The previous version of
    this check compared treasury_end to the next round's treasury_start, which
    run_deterministic_simulation sets equal by construction — so it could never
    fail. This version asserts the equation itself, which is the property that
    catches an engine leaking or double-counting money.
    """
    for lg in ledgers:
        expected = (
            lg.treasury_start
            + lg.csf
            - lg.total_capex
            - lg.loan_interest
            - lg.emergency_credit_interest
            - lg.negative_treasury_interest
            + lg.side_track_treasury_delta
        )
        residual = lg.treasury_end - expected
        assert abs(residual) <= tol, (
            f"INV-1 treasury conservation violated in round {lg.round_number}: "
            f"residual ${residual:,.2f}\n"
            f"  start={lg.treasury_start:,.2f} csf={lg.csf:,.2f} "
            f"capex={lg.total_capex:,.2f} interest="
            f"{lg.loan_interest + lg.emergency_credit_interest + lg.negative_treasury_interest:,.2f} "
            f"side_track={lg.side_track_treasury_delta:,.2f}\n"
            f"  expected_end={expected:,.2f} actual_end={lg.treasury_end:,.2f}"
        )
```

Do the same to the balance sheet: compute equity independently from the net-income roll-forward instead of plugging it, and assert `abs(assets - liabilities - equity) < 0.01`, logging the residual.

**The characterization harness** — `backend/tests/test_financial_golden_trace.py`. This is #9, the highest-value item in the review. It is a clone of the mechanism you already built and proved, pointed at the money:

```python
"""Golden-master trace for the FINANCIAL core.

Companion to test_stakeholder_golden_trace.py, which pins reputation / social
licence / governance / NPC state. This one pins the numbers students are GRADED
on: treasury, EBITDA, emissions, synergy, per-BU revenue and cost, and the two
terminal outputs (M_R and terminal valuation).

This test does not assert the engine is CORRECT. It asserts it is UNCHANGED.
When a deliberate model change alters these numbers, rebaseline with

    MURESSONS_REBASELINE_GOLDEN=1 pytest backend/tests/test_financial_golden_trace.py

and commit the resulting JSON diff IN THE SAME COMMIT as the engine change, so
the review shows exactly which numbers moved and by how much.
"""
import json, os, pathlib, pytest

GOLDEN = pathlib.Path(__file__).parent / "golden" / "financial_trace.json"
SEED   = "muressons-financial-golden-v1"
DP     = 4          # cross-platform float formatting tolerance

GLOBAL_KEYS = (
    "round_number", "corporate_treasury", "historical_ebitda", "tco2e_emissions",
    "synergy_multiplier", "avg_carbon_intensity", "total_ncd", "cost_of_capital",
)
BU_KEYS = ("revenue_base", "opex_base", "carbon_intensity", "absolute_emissions")


def _snapshot(gs, bus):
    return {
        "global": {k: round(float(gs.get(k) or 0), DP) for k in GLOBAL_KEYS},
        # sort by bu_id so backend row-ordering can never move a number
        "bus": {
            bu["bu_id"]: {k: round(float(bu.get(k) or 0), DP) for k in BU_KEYS}
            for bu in sorted(bus, key=lambda b: b["bu_id"])
        },
    }


def _play_ten_rounds():
    """Fixed script, fixed seed, no HTTP, no clock, no I/O."""
    gs, bus = initial_state(stochastic_seed=SEED)
    trace = [_snapshot(gs, bus)]
    for rnd in range(1, 11):
        decisions = SCRIPT[rnd]                       # committed alongside this test
        gs, bus, events = run_one_round(gs, bus, decisions)   # pre_tick→process_tick→post_tick→run_new_engines
        trace.append(_snapshot(gs, bus))
    trace.append({
        "terminal": {
            "m_r": round(calculate_mr(gs, bus, gs["active_event_flags"]), DP),
            "terminal_valuation": round(calculate_terminal_value(gs, bus), DP),
            "archetype": determine_archetype(gs, bus),
        }
    })
    return trace


def test_financial_trace_is_deterministic():
    """Same seed, same script, twice in one process → identical.
    If THIS fails, an un-seeded random source is in the engine path — fix that
    before trusting anything below."""
    assert _play_ten_rounds() == _play_ten_rounds()


def test_financial_trace_matches_golden():
    actual = _play_ten_rounds()
    if os.getenv("MURESSONS_REBASELINE_GOLDEN") == "1":
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n")
        pytest.skip("golden rebaselined — review and commit the diff")
    expected = json.loads(GOLDEN.read_text())
    assert actual == expected, (
        "Financial trace changed. If this was deliberate, rebaseline with "
        "MURESSONS_REBASELINE_GOLDEN=1 and commit the JSON diff in the same commit."
    )


@pytest.mark.parametrize("engine_toggle", [
    "org_politics_enabled", "board_governance_enabled", "supply_chain_network_enabled",
])
def test_seeded_run_is_reproducible_with_every_engine_on(engine_toggle):
    """The stakeholder golden trace disables these three because they roll on the
    bare global `random`. They default to ON in production. This test fails today
    and is the acceptance criterion for remediation #15."""
    a = _play_ten_rounds_with({engine_toggle: True})
    b = _play_ten_rounds_with({engine_toggle: True})
    assert a == b, f"{engine_toggle} introduces un-seeded non-determinism"
```

The last test is the one that changes how the team works: it **fails today**, deliberately, and it is the definition of done for the RNG conversion. Mark it `xfail(strict=True)` so it flips to a hard failure the moment the conversion lands and someone regresses it.

---

## 8. Target architecture and migration path

### Target

```
┌─────────────────────────────────────────────────────────────────────┐
│  UI  (Next.js)                                                      │
│  Renders state and events. Computes NOTHING the engine also         │
│  computes. Every threshold, formula and catalog comes from the API. │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │  HTTP + WS (transport only)
┌─────────────────────────────────┴───────────────────────────────────┐
│  TRANSPORT  routers/*.py                                            │
│  Auth, validation, serialisation, guards, ownership. No rules.      │
│  Every route: a role guard AND a tenant check. Pinned by tripwires. │
└─────────────────────────────────┬───────────────────────────────────┘
┌─────────────────────────────────┴───────────────────────────────────┐
│  APPLICATION SERVICES  services/*.py                                │
│  RunService.commit(run_id, submission, expected_round) -> Result    │
│  RunService.advance(...) / undo(...) / force_advance(...)           │
│  Owns: locking, idempotency, transactions, audit, publication.      │
│  One RunStateMachine owns every transition. Nothing else mutates    │
│  run state. Emits domain events; does not know about HTTP.          │
└──────────────┬────────────────────────────────┬─────────────────────┘
               │                                │
┌──────────────┴──────────────┐   ┌─────────────┴───────────────────┐
│  SIMULATION  sim/           │   │  PERSISTENCE  store/            │
│  PURE. No I/O, no clock, no │   │  One implementation (Postgres). │
│  globals, no config import  │   │  Memory store demoted to a test │
│  at module scope.           │   │  fixture + offline-workshop     │
│                             │   │  mode, value-parity tested.     │
│  resolve(RunState, Submis-  │   │  Append-only rounds; append-    │
│    sion, ScenarioConfig,    │   │  only audit; run_config stamped │
│    Seed) -> (RunState,      │   │  at creation.                   │
│              Events)        │   └─────────────────────────────────┘
│                             │
│  ScenarioConfig is a VALUE, │   Golden traces + invariants live
│  passed in, versioned,      │   against sim/ and run in CI.
│  hashed, stored with the run│
└─────────────────────────────┘
```

The load-bearing change is the arrow into `sim/`: **`ScenarioConfig` and `Seed` become parameters instead of ambient globals.** That single change is what makes replay possible, makes the golden traces meaningful, makes config versioning natural, and removes `engine.py:2616`'s reach into `_god_mode_settings`. Everything else is tidying.

### Migration path — each step ships safely on its own

**Step 0 — Stop the bleeding (1 day, inside the next 5).** Remediation #1–#6, #12, #13, plus #20′ if there is a spare hour. No structural change. Ship before the next run and re-check `/api/health` afterwards.

**Step 1 — Build the net (1–1.5 weeks).** #9 financial golden trace (synthetic script, since §9.6 says there is no recorded run), #10 conservation, #32 RNG-restore fixture, #40 goldens under Postgres, #7 the two guard tripwires, #31 collected full-run HTTP test, #43 persist the full commit envelope so the *next* real run becomes a fixture. Nothing in `sim/` moves. **Exit criterion: `pytest` twice in a row produces identical results, and the golden traces are gating in CI on both backends.**

**Step 1.5 — Make the calibration loop real (4–5 days). New, and it is here rather than later because of §9.7.** #37 config on the durable volume, #38 attribute-access config so hot-reload is honest, #39 carbon-price fallback, #22 CSF pool, #29 `_engine_tunables`, **and §8.1 Phase B — `dry_run.py` wired as a working pre-flight**. Do this immediately after Step 1 and not before: **the golden trace is what tells you whether a number moved because you fixed the plumbing or because a value you had already set finally took effect.** Expect the trace to move here. That diff is the most interesting artifact in the whole programme — it is a list of the parameters you thought you had changed. The pre-flight is the other half: the trace tells you *which number* moved, the dry run tells you *whether the game got harder*. **Note the ordering constraint inside this step: `dry_run` must not be wired until #15 removes the need for its global `random.seed()` call.**

**Step 2 — Make the run reproducible (1–2 weeks).** #14 seed always set, #15 RNG conversion (all 12 sites — all live per §9.10), #18 BU-ordering parity **first**, since production is Postgres and every test is memory-mode, #27 config stamped on the run, #16 CEO-interview. Every one changes observable output; every one is proved by rebaselining the golden with a reviewed diff. **Exit criterion: `replay(session_id)` reproduces the stored terminal state, asserted in CI on a committed fixture run.** **Deadline: before the first graded cohort (§9.1).**

**Step 3 — Extract `sim/` (2–3 weeks).** Move `engine.py`, `round_logic.py`, `balance_sheet.py`, `terminal_valuation.py` and the config tables into a package with **no** imports from `router`, `admin_shared` or `database`. Change `process_tick`'s signature to take `ScenarioConfig` and `Seed` explicitly. Because Step 2 already stamped the config on the run, the caller has both to hand. `_commit_turn_impl` shrinks to: validate → load run → `sim.resolve(...)` → persist → publish. **The golden traces do not change by a single digit.** That is the whole point, and it is how you know the move was clean.

**Step 4 — `RunService` + the state machine (2 weeks).** One module owns lock acquisition, idempotency keys, the transaction boundary, the audit write and the publish. Every one of the 44 `update_latest_global_state` call sites either goes through it or is deleted. #19 audit, #24/#25 transactional fixes, #13 pacing, #28 facilitator work product all land here naturally.

**Step 5 — Split the routers (1–2 weeks, low risk *by then*).** With guard tripwires green and `RunService` owning behaviour, `admin_router.py` becomes a mechanical move: catalogs to data modules first, then `config_admin`, `excel_admin`, `settings_admin`, `god_mode_admin`, `analytics_admin`. Do this last, not first.

**Step 6 — Delete the second implementations (ongoing).** The frontend M_R copy, the case catalog copy, the two glossaries, `_engine_tunables`, `validation_logic.py`, `stakeholder_bulk_excel.py`, the dead auto-pause feature. Serve them from the API or delete them.

---

### 8.1 The four unreachable modules — phased plan

*(Added at your request. These are four different problems wearing the same label, and they belong in three different phases. Two are an hour's work; one is a genuinely valuable instrument you are not using; one is a modelling decision, not a wiring task. Sequencing matters more than effort here — one of them can corrupt a live cohort if wired carelessly.)*

#### Phase A — with Do-Now, before the next run (~2.5 hours total)

**A1. `deploy_preflight.py` → wire it. (30 min, zero risk.)**
This module is good work sitting idle. Five checks, each documented against an incident that actually happened, pure and side-effect free by design, already unit-tested, and explicitly built so that `main.py` decides whether to display the findings. Wiring is five lines in the lifespan, next to the existing storage banner:

```python
# main.py — inside lifespan(), after the storage probe
try:
    from deploy_preflight import run_preflight, format_findings
    print(format_findings(run_preflight()))
except Exception as _pf_exc:          # a preflight must never block a boot
    print(f"[preflight] skipped (non-fatal): {_pf_exc}")
```

Two notes. First, this makes `PREDEPLOY_CHECKLIST.md` Layer 4 true — it currently instructs you to look in the logs for `[preflight] Deployment configuration looks correct.`, a string that can never appear. Second, **[F]** one of its five checks is already satisfied: `TRUSTED_PROXY_IPS` is correctly set to `127.0.0.1,::1,10.0.0.0/8,100.64.0.0/10` at `Dockerfile:59`, so the "one rate-limit bucket for the whole cohort" failure mode is *not* live. The other four — a shipped `master_password.json` overriding your env var, a non-durable data dir, stale state on the volume, `PLAYER_MASTER_PASSWORD` left armed — are all still worth hearing at boot. Expect the first run to surface at most one finding, since `/health` already confirms your data dir is durable.

**A2. `scale_preflight.py` → not broken; make it undeletable. (30 min, zero risk.)**
This one is a false positive in my own analysis and the fix is to stop it being one. It runs on every boot via `docker-start.sh:21` (`python -m scale_preflight`), and its logic is sound: clamp `WEB_CONCURRENCY` to 1 unless the shared Postgres backend is active, print the number on stdout and warnings on stderr so the shell can capture the former cleanly. The entrypoint even has a correct fallback — a non-integer result defaults to 1. **The defect is that it is invisible to every static tool**, so the next dead-code sweep (including the one I just ran) proposes deleting the module that decides your worker count. Fix:

```python
# backend/tests/test_entrypoint_wiring.py
def test_docker_start_invokes_scale_preflight():
    """scale_preflight is reached only via `python -m scale_preflight` in the
    container entrypoint, so no import graph can see it. This tripwire is the
    only thing standing between it and a dead-code sweep."""
    entry = (REPO / "docker-start.sh").read_text()
    assert "python -m scale_preflight" in entry
```

Add the same for any other out-of-band entry point, and put a one-line "invoked from docker-start.sh, not imported" note at the top of the module.

**A3. `market_dynamics.py` → unadvertise the toggle. (1 h, zero risk.)**
Do **not** wire it now — see Phase C. But do not leave a facilitator-visible switch that silently does nothing either. Remove `market_dynamics_enabled` from `CreateCohortModal.js:77` and `GodModeStatus.js:391`, or — better, since you may want it later — render it disabled with the label "Coming soon" so the intent survives in the UI without promising behaviour. Leave the module and the setting plumbing (`admin_router.py:521,609`) in place; they cost nothing and are the scaffolding for Phase C.

**A4. `dry_run.py` → disable the button. (30 min, zero risk.)**
The `DryRunSimulator` tab currently 404s on click. Hide the tab until Phase B lands. This is the smallest of the four changes and the one a facilitator is most likely to hit by accident.

#### Phase B — inside Step 1.5, after the golden trace: `dry_run.py` becomes your calibration instrument

**This is the item worth being enthusiastic about.** Given §9.7 — you retune daily, alone — a pre-flight that flies four bot strategies through the *real* engine from a cohort's current state to Round 10, over seeded repetitions, and returns a difficulty grade with per-strategy trajectories and a crisis-bite table, is precisely the missing half of the calibration loop. The golden trace tells you *whether a number moved*; the dry run tells you *whether the game got harder*. Together they close the loop that Dimension L says is currently open. The module is already written and the frontend already exists.

**But it cannot be wired as-is, and the reason is serious. [F]** `dry_run.py:119`:

```python
    strategy = STRATEGIES[strategy_id]
    rng = random.Random(seed)
    random.seed(seed)  # engines that roll on the bare global random module
```

`random.seed()` mutates the **process-global** PRNG. Every one of the twelve unseeded engine sites (§4.A) draws from that stream, and **you run all of them (§9.10)**. So a facilitator pressing "Run pre-flight" during a live workshop **rewinds the random number generator for every cohort in that worker** — 4 strategies × N reps times over. The module's own docstring claims it is *"Pure & side-effect free… NOTHING is persisted."* The first clause is false in the way that matters most.

Ordered fix:

1. **Remove the global reseed** (`dry_run.py:119`). It exists only because the twelve engine sites bypass `event_rng`. So **#15 is a hard prerequisite** — once every draw goes through the seeded stream, the line is unnecessary rather than merely dangerous.
2. **Replace `hash(sid)`** at `dry_run.py:230` with a stable digest (`int(hashlib.sha256(sid.encode()).hexdigest()[:8], 16)`). `PYTHONHASHSEED` is unset everywhere in the repo, so today the difficulty report changes on every backend restart — which for a daily calibrator is worse than no report.
3. **Then** add the route the frontend already calls — `POST /api/admin/dry-run`, body `{session_id, n_reps}`, guard `require_sim_manager` **plus `_assert_session_ownership`** (it reads a cohort's live state).
4. **Offload it.** 4 strategies × 3 reps × 10 rounds ≈ 120 synchronous `process_tick` calls. At `WEB_CONCURRENCY=1` that blocks every other request for the duration. `run_in_executor`, and cap `n_reps` server-side. This shares the fix with #33.
5. **Refuse to run it against a cohort mid-round** — or at minimum warn — until (4) lands.

**Acceptance test:** run a dry run, then assert that a subsequent seeded `process_tick` on an unrelated session produces byte-identical output to the same tick without the dry run. That is the test that proves the side effect is gone, and it is the reason to do this after #15 rather than alongside it.

#### Phase C — Structural, gated: `market_dynamics.py` is a modelling decision

**The panel splits on this one, and the split is worth reading.**

**SE:** *it is 307 lines with zero call sites and zero tests. That is not a fix, it is a new feature. Treat it as one — schedule it, spec it, test it — and do not let "we already wrote it" become the reason to ship it.*

**PA:** *it is also the only cross-player mechanic in a product sold as multiplayer. Shared talent pools, a competitive carbon-permit price, market share that sums to one — that is the pedagogical difference between twenty people playing solitaire in the same room and a cohort playing a market. It is worth scheduling properly rather than deleting.*

**SMP, and this is the argument that decides the sequencing:** *wiring it changes what "a reproducible run" means.* Today every team's outcome is a pure function of that team's own decisions, so `replay(session_id)` — the exit criterion for Step 2 — is well-defined per team. `process_market_tick` makes each team's result depend on **every other team's commits**, which means replay becomes cohort-scoped: to reproduce one team you must reproduce all twenty, in the order they committed. That is a defensible design and arguably a better simulation, but it is a decision to take deliberately and *after* Step 2, not a wiring task to slot in.

**And there is a structural blocker.** `market_dynamics.py:18` says the shared state is *"updated after each round when all players have committed."* **Muressons has no such hook.** Rounds advance per team; the only "all teams committed" signal is `_cohort_advance_status`, which lives on the read path and fires on whoever polls first (finding #44). **So the module is dormant because the architecture never grew the seam it was written against.** That makes the dependency chain explicit:

> **#44** (barrier off the read path, into a cohort-scoped task owned by `RunService`) → **Step 2** (per-team replay proven) → **decide** whether cohort-scoped replay is acceptable → **then** wire `market_dynamics`, with its own golden trace covering a full cohort.

If the answer at the decision point is "no", delete the module and the toggle and stop carrying them.

#### Summary

| Module | Phase | Action | Effort | Behaviour risk |
|---|---|---|---|---|
| `deploy_preflight.py` | **A — Do-Now** | Wire into `main.py` lifespan | 30 min | None |
| `scale_preflight.py` | **A — Do-Now** | Not broken. Add an entrypoint tripwire so it survives dead-code sweeps | 30 min | None |
| `market_dynamics.py` | **A — Do-Now** | Unadvertise the toggle (disable, don't delete) | 1 h | None |
| `dry_run.py` | **A — Do-Now** | Hide the tab that currently 404s | 30 min | None |
| `dry_run.py` | **B — Step 1.5** | Fix the global reseed + `hash()`, add the route, offload to a thread. **Gated on #15.** Becomes your calibration instrument | 1 day | ⚠️ Low — but *unfixed* it is High, because it rewinds live cohorts' RNG |
| `market_dynamics.py` | **C — gated** | Decide, then wire or delete. **Gated on #44 and Step 2.** Changes replay from per-team to per-cohort | 1 week + decision | ⚠️ High — new cross-player coupling |

---

## 9. Your answers, and what each one moved

Recorded verbatim, with the effect on the review. Items marked **[F]** are now facts and the corresponding **[A]** assumptions have been struck from the body.

1. **Grading — "not yet used in grading." [F]** Converts §A/§E from an active academic-integrity exposure into a closing window. #16 High → Medium. It also sets the real deadline for the Foundation and Step-2 blocks: **before the first graded cohort**, which is a date you control.
2. **Production config — "not sure."** Resolved for you by direct measurement (see the housekeeping block): **PostgreSQL, `demo_mode: false`, `/data` mounted, writable and durable, `/docs` correctly 404.** That is the right configuration. It also confirms three findings as live rather than conditional: `_fa_force` self-reversion (#13), the three phantom writes under Postgres (`max_round` pace lock, `round_deadline`, commit notifications), and the BU-ordering divergence (#18). **[A] still open:** `WEB_CONCURRENCY` — worth one `railway variables` check.
3. **Next run — 7 days in your message, 5 days in your comment on the draft; 10 people in the room. [F]** I have planned Do-Now for **five** days, since that is the tighter read; if it is seven, you get slack rather than a scramble. Ten people means the capacity work (#33) is genuinely deferrable for this run.
4. **Backups — "yes." [F]** #20 drops off Do-Now. Replaced by **#20′: rehearse one restore**, because an untested backup is a belief rather than a control — and you have already lost a database once.
5. *(No answer given — this was the "second engineer" question; carried forward to §10.)*
6. **Recorded run — "No." [F]** The golden master in Step 1 must be a **synthetic committed script** rather than a captured cohort. That is cleaner (deterministic by construction) but weaker in one respect: it pins current *code* behaviour, not behaviour a real cohort experienced. Hence new item **#43** — persist the full commit envelope now, so the *next* run becomes a real fixture for free.
7. **Retuning — "every day, by myself." [F]** The single most consequential answer. It created **Dimension L**, promoted #22 and #29 into Foundation, and added #37/#38/#39. It also reframes the golden trace: for you it is not primarily a regression net, it is **the instrument that tells you whether the parameter you just changed did anything.** That is a daily-use tool, not a CI checkbox.
8. **Deployment — "Railway is used for workshops." [F]** Removes the operational case for the in-memory backend and **reverses my "deliberately not doing" call** on it (see the rewritten entry). Adds #40.
9. **Scale — "max 20 teams/players at a time in a cohort; only one member per team has edit and input rights, the others are observers, up to 6 per team; multiple cohorts may run simultaneously." [F, corrected in Rev 3]**

   You were right to push back on my "120 players playing simultaneously" framing, and half-right about the consequence. I have split the number, because the two halves behave differently:

   - **Writes: 20.** Unchanged — I had already sized the pool and CPU arithmetic on 20 committing drivers, so that analysis stands. The binding constraint is **~60 serial synchronous ticks** in the closing seconds of a round (20 commits × `process_tick` + two decision-regret shadow ticks), on one event loop at `WEB_CONCURRENCY=1`. Observers cannot make this worse.
   - **Reads: not reduced by the correction.** Poll load is driven by *connected browsers*, not by edit rights. **[F]** An observer signing in with `MUR-004-VIEW` resolves to the same `session_id` and lands in the same cockpit; `GET /dashboard` is the one route opened to them (`router.py:1868`, the only `allow_observer=True` in the file); and the 5-second poll (`useSimulation.js:640-690`) has **no observer gate**. So a team watching on six laptops is six full-rate pollers, and each poll costs ~40 sibling queries. 20 devices ≈ 160 q/s; 120 devices ≈ 960 q/s.

   **Confirmed: 6 per team = 1 driver + 5 observers**, each on their own laptop. The figures above are unchanged — that is what they were sized on.

   **One implication of the seat model worth knowing. [F]** All five observers share **one** credential: a single `MUR-004-VIEW` code with a single bcrypt-hashed `team_view_password` (`admin_router.py:4386-4395`), with no cap on concurrent use. So the system cannot tell your five observers apart — there is no per-observer identity, no attendance record, and nothing linking a named student to a seat. Three consequences: (a) if participation ever feeds a grade, the observer seats contribute no evidence; (b) the peer-evaluation feature is per-named-person, and observers have no name to evaluate against; (c) a view code that leaks — screenshot, shared chat, photographed slide — lets an unbounded number of people watch that team's live board for the rest of the term, since the codes are per-team and long-lived. None of this is urgent, and the shared-code design is a defensible simplification. It just means the observer seat is a *viewing* mechanism, not an *identity* mechanism, and should not be leaned on for anything assessment-related.

   **And a warning for whoever applies the Finding 1 fix:** `router.py:767` — `join_session(..., _bypass_password=_as_observer)` inside `player_login` — is the **one legitimate caller** of that parameter, and it is how observer login works after the view code has been verified against `team_view_password`. Exemplar 1's refactor preserves it deliberately (`_join_session_impl(..., bypass_password=True)`). Delete the parameter outright instead of making it keyword-only and **you will break every observer seat.**

   So the discriminating fact is not permissions, it is **devices** — see §10.4. If observers watch over the driver's shoulder on one screen, my original figure was simply wrong and read load is fine. If they each sign in on their own laptop (which is what the `-VIEW` feature exists to enable), the figure holds.

   **And checking this turned up a defect I had missed** — new item **#44**, and a new drill row. `get_dashboard` calls `_cohort_advance_status`, which calls `_auto_commit_laggards` (`router.py:1910` → `:508`). The barrier and the free-advance timeout are enforced **on the read path**, by whoever polls first. Since observers can call `get_dashboard`, **a spectator's browser can force-commit a different team's round.** The observer seat is otherwise a well-built, fail-closed design — it refuses every mutation on all 27 other player routes — and the mutation happens anyway, one call frame down, because a GET was given a side effect. The mirror image is equally bad: with nobody polling, Force Advance and the round timeout never fire.

   Cross-tenant is now scheduled rather than theoretical (items #41/#42). And note `MAX_PLAYERS_CEILING = 20` with its own docstring: *"a cohort larger than this has never been exercised by the round engine's peer-comparison or leaderboard paths."* **Your stated maximum is exactly the untested edge**, so the first 20-team run is itself a test.
10. **Engines — "all the engines are run." [F, and you asked me to name the dormant ones.]**

    **Fair challenge — I never named any.** In the draft I *asked* whether some were dormant and hoped so; I had not done the work. I have now. I built the import graph from `main.py` across all 97 top-level backend modules and traced reachability. **91 of 97 are reachable, so you are essentially right: the engines all run.** Six are not reachable, and only one of them is an engine:

    | Module | LOC | Status |
    |---|---|---|
    | `scale_preflight.py` | 86 | **Not dead — keep.** Invoked out-of-band by `docker-start.sh:21` (`python -m scale_preflight`). The import graph can't see it; it runs on every boot. |
    | **`market_dynamics.py`** | **307** | **The one genuinely dormant engine — and it has a live UI switch.** No backend module imports it. Meanwhile `market_dynamics_enabled` is a per-cohort toggle rendered in `CreateCohortModal.js:77` and `GodModeStatus.js:391`, with the tooltip *"Cross-player market: shared carbon credit pool, competitive talent hiring, scarcity pricing."* It defaults to `False`, it is plumbed through `admin_router.py:521,609` into cohort settings — and ticking it does nothing at all. **This is a fifth instance of the Dimension L pattern**: a control that reports success and is not wired to the engine. Either wire it or remove the toggle; leaving a facilitator-visible switch that silently no-ops is the worst of the three options. |
    | `validation_logic.py` | 1001 | **Dead. Delete.** Zero references anywhere in the repo outside itself. Despite the name it is an E2E HTTP harness, not a validator. |
    | `stakeholder_bulk_excel.py` | 448 | **Dead. Delete.** Superseded — its only mention is a comment at `excel_dropdowns.py:89` explaining that the current code deliberately does *not* use it. |
    | `dry_run.py` | 328 | **Dead backend, live frontend.** `DryRunSimulator.js` is a facilitator tab that POSTs to `/api/admin/dry-run`, and no such route exists → 404 on click. Wire it or delete both. (Careful: the other `dry_run` hits in the frontend are an unrelated Excel-preview flag.) |
    | `deploy_preflight.py` | 186 | **Dead, but should be wired, not deleted** — see #34. Its checks are good and `PREDEPLOY_CHECKLIST.md` instructs operators to look for output it can never produce. |

    So: **~1,777 LOC to delete outright** (`validation_logic`, `stakeholder_bulk_excel`, plus `dry_run` if you don't want the feature), **one dormant engine to wire or unadvertise**, and **one module to switch on**. Modest, but the `market_dynamics` toggle is worth knowing about before a facilitator ticks it in front of a cohort and wonders why nothing happens.

    **Scope caveat:** this is *module*-level reachability. It does not find dead functions inside live modules. Those I found separately and by hand: `check_auto_pause_triggers` (`admin_router.py:10975`, zero callers — the whole auto-pause feature and its config endpoints are inert), `reload_simulation_config` (`config.py:640`, zero callers), `auth_jwt._decode_token_ignore_expiry` (never called), `database_memory._async_write_lock` (declared, never used), and the EU AI Act rule at `round_logic.py:1834` (unreachable in normal play). A systematic dead-function sweep is a half-day with `vulture` and would likely find more.

    The answer also confirms the thing that matters most: all 12 unseeded RNG sites are live in every session, including the three engines the golden trace switches off to stay green.

**Assumptions that remain:**

- **[A]** CI is green and gating. `ci.yml` exists and is tracked, but branch protection and Railway "Wait for CI" live outside the repo — and the file is locally modified and uncommitted.
- **[A]** Students have seen CEO-interview scores as *formative* feedback even though nothing was graded. If so, some of that feedback was literally random.
- **[A]** No participant has yet asked how a number was derived. That request is what converts §E from debt into an incident.
- **[A]** Where the `AUDIT_*` / `IMPLEMENTATION_*` documents and the code disagree, I trusted the code.

---

## 10. Follow-ups — answered, and the one still open

### 10.4 (answered) — "I use any one of all three"

You retune through the **Excel importer**, the **god-mode sliders**, *and* by **editing `simulation_config.json` and redeploying**. That is the worst of the three possible answers, and it means **#37 and #38 stay High** rather than dropping to Medium. Each path fails differently, and — the part that matters — **they overwrite each other silently.**

| Path | What actually happens |
|---|---|
| **Edit `simulation_config.json` + redeploy** | **This is the only path that fully works.** A redeploy is a fresh process, so every `from config import X` binding is rebuilt correctly, and the file is committed, so it survives. |
| **Excel importer** | Writes to the **image** filesystem (`runtime_paths.py:24-26` excludes config from `/data`), so **the next redeploy silently reverts it** — including a redeploy you do for an unrelated code fix. Hot-reloads only 5 modules; `round_logic.py`, `router.py` and ~8 others keep their old constants, and `router.py:19` still points at the old `process_tick` object. Reports `{"reload":"complete"}` regardless. Covers 194 of 203 parameters and omits the CSF pool entirely. |
| **God-mode sliders** | `_engine_tunables`: **22 of 24 values are write-only.** The 2 that work (`overrun_probability`, `overrun_severity`) land in `_god_mode_settings`, which is a process-global dict read *mid-tick* at `engine.py:2616` — not persisted per run, not in the run record, and **shared across every concurrent cohort**. |

**The compound failure is the one to internalise:** tune via Excel on Monday, push a code fix on Wednesday, and Monday's tuning is gone — with no message, no diff, and no way to tell from the UI. Meanwhile a slider you moved may have been inert, and the sliders that weren't are affecting other people's cohorts.

**Two consequences for the plan.** First, until Step 1.5 lands, **use only the third path** — edit the JSON, commit, redeploy. It is slower and it is the only one that means what it says. Second, this created **#47**: a `GET /api/admin/config/live` endpoint that reports the engine's *in-memory* constants with each value's resolved source and a fingerprint hash. With three tuning surfaces that can disagree, "did my change take?" needs to be a question you can *look up* rather than infer from output — especially since determinism (§4.A) has already made inferring-from-output unreliable.

### 10.5 (answered) — observers use their own laptops

That settles the read-path question and removes the conditional from §4.D. At full scale: **20 teams × 6 laptops ≈ 120 pollers ≈ 550 queries/second** just for the "X/Y committed" badge. Two consequences: **#46** (per-cohort cache — an ~80× reduction for ~30 lines, and the cheapest capacity win in this document) and a bump in urgency for **#44**, since with six observer browsers per team it becomes *likely*, not merely possible, that a spectator's poll is the thing force-committing another team's round.

### 10.3 (explained) — what `WEB_CONCURRENCY` is, and why I asked

Sorry — that was jargon. Plainly:

Your backend can run as **one process** handling every request one at a time, or as **several copies of itself** ("workers") sharing the load. `WEB_CONCURRENCY` is the setting that decides how many. Railway stores settings like this as **environment variables** — key/value pairs injected when the container starts. `docker-start.sh:21` reads it at boot and passes it to the web server.

**Why it matters here.** Large parts of Muressons keep state in ordinary Python dictionaries that live *inside one process* — the player-id counter, the facilitator-id counter, the cohort quota check, the rate-limit buckets, facilitator notes and bonuses, the pacing dictionary. With one worker there is one copy and everything is consistent. With two workers there are **two separate copies that never talk to each other**, so: two facilitators created at the same moment can both get `FAC-007`; two students can both be minted `MUR-001`; the rate limit becomes twice as permissive; and a facilitator's notes exist only on whichever worker served that request. Your code is written correctly for one worker — this is not a latent bug, it is an assumption that stops holding.

**You are almost certainly fine.** `scale_preflight.py` refuses to fan out unless Postgres is active, and the default is 1. But it *will* honour a higher value now that you are on Postgres — which is exactly the configuration where someone raising the number "for performance" would look reasonable and quietly break the classroom.

**How to check — no CLI needed.** In the Railway dashboard: open your project → click the backend service → **Variables** tab → look for `WEB_CONCURRENCY` in the list. If it is absent, or set to `1`, nothing in this review changes. If it is `2` or more, tell me and four findings move to Do-Now immediately. (If you do have the CLI installed, `railway variables` prints the same list, and `| grep WEB_CONCURRENCY` just filters it to that one line.)

While you are on that screen, two others are worth a glance: `DEBUG` should be `false` or unset — if it is `true`, internal error tracebacks are returned to players (`main.py:473-482`) — and `ALLOW_MEMORY_DB_IN_PROD` should be unset. `/health` already confirms the second is effectively fine.

### 10.1 (answered) — a second engineer is coming

Then **Step 5 goes back on the roadmap.** I had recommended dropping the router split entirely on the grounds that you are the constraint and a move-only refactor of a 12,492-line file buys you nothing. With a second person that inverts: `admin_router.py` at 232 endpoints across 55 responsibility sections is exactly what makes a new hire slow, and — because only ~30 of those endpoints carry an ownership check — dangerous. #7 (the two RBAC guard tripwires) rises with it, since they are what turns the split from a game of spot-the-missing-`Depends` into a mechanical move.

Dimension K also stops being a note and becomes a plan. **Give them #7, then #35 + #45 in week one** — dead-code removal and the dormant `market_dynamics` toggle. Isolated, zero behaviour risk, and it forces a read of the import graph, `CLAUDE.md` and the tripwire suite, which is the fastest honest tour of this system. **Do not give them a rule change until the golden traces exist** — §4.B lists nine things they would have to know first, and six of them are only discoverable by having been burned.

One thing to write down before they arrive: **which of the six copies of the M_R formula is authoritative** (`terminal_valuation.py:175`), and that the comment twelve lines into the authoritative R10 function states the wrong coefficient and the wrong maximum. That single fact is the highest-value sentence in your onboarding doc.

### 10.2 (answered) — graded, 20 teams, 2 weeks, single cohort

The full re-plan is **§6.05 and §6.1**. Headline: a hard 14-day deadline on the determinism block; **#16 back to High** (it is graded now); **#41/#42 off the critical path** (single cohort is a real reprieve); **#46/#33 onto it** (120 pollers and the untested 20-team ceiling arrive on the same day). If you slip, slip the capacity work and cap the first graded cohort at 10 teams — never slip the determinism block.

### Still open

Nothing blocking. Two worth a glance when you have five minutes: the `WEB_CONCURRENCY` check in §10.3, and whether CI is actually gating — **§Housekeeping item 3 is the argument for that one**: a tripwire that is red on your disk and that nothing runs is not a control.

