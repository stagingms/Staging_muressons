# AUDIT — Railway Readiness, Redundancy & Fidelity (2026-07-19)

Every finding below was **verified against the code or live data in this
session** (file:line cited). Candidates that did not survive verification were
discarded — e.g. the suspected `/api/health` healthcheck mismatch is NOT an
issue (`frontend/app/api/health/route.js` exists and Next route handlers take
precedence over rewrites), and R10 decisions ARE persisted (94-row decision
log contains 9 round-10 rows) despite the dead loop that implies otherwise.

Deployment context that raises the stakes: `docker-start.sh` defaults
`USE_MEMORY_DB=false` — **Postgres is the default store on Railway** — and
`scale_preflight` allows multiple uvicorn workers *only* under Postgres. So
"works in memory mode" is exactly the wrong test for production.

---

## SEVERITY 1 — Breaks on Railway's default (Postgres) configuration

### 1.1 Eight admin endpoints read the in-memory store directly → silently empty under Postgres
- **Location:** `backend/admin_router.py` lines 8168, 9070, 9124, 9198, 9279,
  9622, 9679, 9730 (`getattr(db, '_sessions', {})` / `_global_states` /
  `_bu_states`); same pattern in `backend/admin_analytics.py:295-297` and
  `backend/admin_teleprompter.py:1051` (`import database_memory`).
- **Issue:** Under Postgres, `database.py` has no `_sessions` module global, so
  `getattr(..., {})` returns an empty dict and these endpoints return empty
  data **with a 200 status** — no error, no log. Affected surfaces:
  Situation-Room bulletin, Complexity Events (both), Session Health, Clone
  Session, Cross-Paradigm Comparison, Cohort Comparison, **Cohort Pulse**
  (live player-facing panel via `CohortPulse.js`), the analytics tabs in
  `admin_analytics`, and the live agent teleprompter. This is the documented
  Section-A debt of `AUDIT_guards_and_memory_stores.md`, still open.
- **Remediation:** Port each read to the async db API that both stores
  implement (`db.fetch_all_sessions()`, `db.fetch_latest_state(sid)`,
  `db.fetch_round_history(sid)`), exactly as was already done for undo-round,
  decision-history and agent_summary. Mechanical, endpoint-by-endpoint;
  no schema work. Add a CI grep-tripwire that fails on
  `getattr(db, '_` and `import database_memory` outside `database_memory.py`
  itself, so the class of bug cannot regrow.

### 1.2 Player-flow logic bound to the memory store
- **Location:** `backend/router.py:397/454` (`set_username` iterates
  `database_memory._sessions` for username uniqueness + propagation),
  `backend/router.py:6119` (`get_player_annotations` reads
  `db_mem._sessions` to resolve the parent cohort & visibility toggle),
  `backend/router.py:805` (join-consent timestamp write, try/except no-op).
- **Issue:** Under Postgres: username uniqueness silently checks an empty
  dict (collisions admitted), annotation visibility resolves against a
  missing session (falls back wrongly), consent timestamps are never
  recorded. These are player-facing correctness failures with no error
  surface.
- **Remediation:** Same as 1.1 — replace with `db.get_session_info()` /
  `db.fetch_all_sessions()`; add a `db.update_session_fields()` helper for the
  consent stamp. These three are the priority ports because they sit in the
  player path, not admin tooling.

---

## SEVERITY 2 — Concurrency & process-state hazards

### 2.1 Dry-run reseeds the process-wide RNG from a worker thread
- **Location:** `backend/dry_run.py:119` (`random.seed(seed)`) called via
  `asyncio.to_thread` in `backend/admin_router.py:5177`.
- **Issue:** `random` is process-global. A dry-run running concurrently with a
  live commit (a) makes the live cohort's stochastic events partially
  deterministic/correlated, and (b) destroys the dry-run's own determinism
  guarantee. Verified by code inspection; the engine rolls on the bare
  `random` module in several sub-engines, which is why the seed is set at all.
- **Remediation:** Remove `to_thread` (a full run measures 0.2 s — verified —
  so blocking the event loop briefly is acceptable and makes interleaving
  with commits impossible on a single worker), and wrap the run in
  `state = random.getstate() … random.setstate(state)` so the live RNG stream
  is bit-for-bit unaffected. For multi-worker deployments this is already
  safe because each worker has its own interpreter.

### 2.2 Custom Black Swan log: per-process, unbounded, non-durable
- **Location:** `backend/admin_router.py:4888` (`_custom_black_swan_log = []`,
  plain `.append` at 5032; contrast `_capped_append` used for the audit log).
- **Issue:** With Postgres + `WEB_CONCURRENCY>1` (which `scale_preflight`
  permits), the injection history a facilitator sees depends on which worker
  served the request; all history is lost on every redeploy; the list grows
  without bound.
- **Remediation:** Persist through the existing `_audit()` channel (it already
  records `custom_black_swan_injected` — verified at admin_router.py:5024) and
  serve the log endpoint FROM the audit store instead of the ad-hoc list;
  delete `_custom_black_swan_log`.

### 2.3 Commit cooldown is per-worker; timestamp dict never shrinks
- **Location:** `backend/router.py:126/1674/1681` (`_commit_timestamps`).
- **Issue:** The 5-second commit cooldown is enforced per process, so with
  multiple workers a client can bypass it by round-robin. Correctness is NOT
  at risk — the Postgres advisory lock (CON-1) still serializes commits — so
  this is a rate-limit gap plus a slow, unbounded dict.
- **Remediation:** Accept the gap (documented) or move the cooldown check
  behind the advisory lock using a `last_commit_at` column; either way, prune
  entries older than an hour on each insert (3 lines).

---

## SEVERITY 3 — Simulation fidelity (educational accuracy)

### 3.1 Balance sheet reports deeply negative cash with zero short-term debt
- **Location:** `backend/balance_sheet.py:527/840` (cash synced raw from
  `corporate_treasury`; `short_term_debt` exists at :226 but is never used as
  a sweep target). Evidence: live cohort statement shows *Cash & Equivalents
  −$478.5M* alongside *Short-Term Debt $0*.
- **Issue:** Negative cash is an accounting fiction — a real group funds a
  cash deficit with borrowing, which appears as a liability and accrues
  interest. For a tool teaching students to READ a Statement of Financial
  Position, this materially miseducates: total liabilities are understated by
  the entire deficit and D/E, liquidity ratio and covenant readings are
  computed off the fiction.
- **Remediation (deterministic):** In `process_balance_sheet_tick`, after the
  treasury sync: `deficit = max(0, -cash); cash = max(0, cash);
  short_term_debt += deficit`, and charge `deficit * loan_interest_rate/2`
  per half-year round to opex (rate already exists in flags). Rebaseline the
  balance-sheet tests in the same commit. Note this changes displayed
  figures, not engine treasury math — the treasury remains the engine truth.

### 3.2 Frontend duplicates the crisis catalog, and it has already drifted
- **Location:** `frontend/app/components/warMapModel.js:43-51`
  (`ROUND_CRISIS`, e.g. "AI bias scandal") vs
  `backend/round_configs.get_round_crisis(6)` ("AI Hiring Bias Scandal");
  the frontend's strike locations are invented client-side.
- **Issue:** Two hand-maintained sources of truth for the same pedagogical
  content; wording has already diverged. Same failure class the shockwave
  catalog tripwire was built to prevent.
- **Remediation:** Emit `{round, title, icon}` from `get_round_crisis()` in
  the `/api/admin/war-map` payload; keep only coordinates keyed by round in
  the frontend. Alternatively add a jest tripwire that parses both, mirroring
  `__tests__/shockwave-catalog.test.js`.

### 3.3 Dry-run "crisis bite" mislabels decision rounds as crises
- **Location:** `backend/dry_run.py` crisis_bite loop —
  `get_round_crisis(1)` returns "ESG Audit Decision" (a decision gate, not a
  shock); verified output shows R1/R2 listed with POSITIVE median deltas.
- **Issue:** The report tells a facilitator that Round 1 is a "crisis" that
  *added* ~$11M — noise that undermines trust in the new tool's headline
  purpose (which rounds bite).
- **Remediation:** Filter the table to rounds whose crisis config carries
  negative-impact semantics, or maintain an explicit shock-round set
  ({3,4,5,6,8,9,10} for legacy_abc, sourced from round_configs), and rename
  the section "Round pressure map" if all rounds are kept.

---

## SEVERITY 4 — Slop & redundancy (maintenance cost, no runtime failure)

### 4.1 Dead code with a misleading comment
- **Location:** `backend/router.py:2228-2230` — `for dec in decisions_raw:
  pass  # decisions are logged inline…`.
- **Issue:** A no-op loop whose comment implies R10 decisions are handled
  here; they are actually persisted elsewhere (verified: decision_log holds
  round-10 rows). Classic vibe-code residue that misdirects the next reader.
- **Remediation:** Delete the loop; replace with a one-line comment stating
  where R10 decisions are actually logged.

### 4.2 Superseded prediction heuristic retained with zero callers
- **Location:** `backend/pedagogical_engine.py` —
  `create_prediction_entry` / `evaluate_prediction` (keyword-sentiment
  "calibration"). Verified: zero non-test callers.
- **Remediation:** Delete both; the deterministic `score_prediction` path is
  the only consumer surface.

### 4.3 Analytics card registry duplicated across two components
- **Location:** `frontend/app/components/AnalyticsControlPanel.js`
  (`FACILITATOR_ANALYTICS`) and `frontend/app/components/PlatformAnalytics.js`
  (`TABS`) — same keys, separately hand-written tooltip copy.
- **Issue:** Every new card must be added twice (empirically true: the
  calibration card required both edits); tooltip wording can drift per
  surface.
- **Remediation:** Export one registry (key, label, icon, tooltip) from a
  shared module; both components import it. ~30-line refactor.

### 4.4 God files — decomposition stalled
- **Location:** `admin_router.py` 10,948 lines; `router.py` 6,317;
  `ExecutiveCockpit.js` 4,382; `engine.py` 4,207. Branch is literally named
  `refactor/decompose-god-files`; the last decomposition commit is a `wip`.
- **Issue:** Not a runtime bug, but it is the single biggest driver of the
  Severity-1 class above: store-access patterns can't be policed in a
  10k-line file. Every audit finding in this document lives in one of these
  four files.
- **Remediation:** Resume the decomposition with a rule, not a rewrite:
  new endpoints land in domain modules (the `admin_analytics.py` /
  `admin_teleprompter.py` split pattern already exists); add the 1.1 CI
  tripwire so extracted modules stay store-clean.

### 4.5 `print()` logging in production paths
- **Location:** 21 occurrences each in `backend/round_logic.py` and
  `backend/admin_router.py` (e.g. engine-failure warnings).
- **Issue:** Engine-failure warnings (`[WARN] … engine failed`) go to stdout
  without level/context — on Railway these are the exact signals you'd want
  to alert on, and they're invisible to log-level filtering.
- **Remediation:** Mechanical swap to the existing `muressons.*` loggers.

---

## Explicitly verified as NOT issues
- Railway healthcheck path (`/api/health` served by
  `frontend/app/api/health/route.js`).
- R10 decision persistence (decision_log contains round-10 rows).
- JWT secret durability (persisted via `runtime_paths`; volume requirement is
  already documented in `DEPLOYMENT_CHECKLIST.md` §2).
- Predictions-log Postgres parity (writes both flag & top-level
  representations; Postgres update path packs top-level keys into flags —
  `database.py:877-885`).
- CORS (env-driven allowlist + `RAILWAY_PUBLIC_DOMAIN` auto-append,
  enumerated methods/headers).

## Recommended order of attack
1. §1.1 + §1.2 store-access ports with the CI tripwire (deploy-blocking).
2. §2.1 dry-run RNG isolation and §2.2 black-swan log durability (small).
3. §3.1 negative-cash sweep (fidelity; touches tests).
4. §3.2/§3.3 crisis-catalog unification + dry-run filter.
5. §4.x slop passes, folded into the resumed god-file decomposition.
