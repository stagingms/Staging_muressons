# Launch blockers — implementation notes (branch `fix/launch-blockers`)

**Scope, phase 2 (top of this file):** items 1–8 of AUDIT_Independent_Review_2026-09-01.md
§8 "Must change before a 30-cohort launch" (F-01, F-02, F-03+F-15, F-20/F-21, F-22, F-26,
F-27, F-37), plus one Critical found while verifying the fixes on Postgres (F-40) and two
small hardening items the same code paths exposed (F-24).

**Scope, phase 3 (second half of this file, from "Phase 3"):** items 9–18 — everything in
§8 "Should change soon" (F-04, F-05/F-06, F-07, F-11, F-08/09/10/12/13, F-23/F-24,
F-16/17/18, F-19/F-36) and "Can wait" (F-28–31, F-32–35, F-38/39) — plus two findings
made while doing it (F-41, F-04b) and a harness fix to the balance runner. Same branch,
still uncommitted, for review.

**Design decisions taken from the review conversation:** BU reputation is the stock and
`group_reputation` is derived from it; CBAM at $100/t; ID-derived default passwords kept
but the change is enforced server-side.

**Test status at hand-over**

| Suite | Result (after phase 3) |
|---|---|
| Backend, memory store (`pytest tests/`, CI job 1) | **2311 passed**, 2 skipped, 0 failures (2253 at the baseline; `tests/test_launch_audit_2026_09_01.py` now carries 60 tests in 22 classes) |
| Backend, real Postgres (the CI parity job's file list, incl. the extended `test_postgres_parity.py`, plus `test_backend_parity_surface.py`) | **116 passed** (11 + 105) |
| Frontend jest | 1098 passed, 4 skipped, **1 pre-existing failure** (`player-visibility-wiring.test.js` "briefing video" — its regex trips on a `}` inside a comment in `admin_shared.py`; fails identically on the untouched baseline) |
| Frontend eslint on touched files | no new problems; the 8 errors reported are all baseline (`RegulatoryShockModule.js:237`, `SideTrackPanel.js:131/496` unescaped entities; `RoundBriefing.js:231–244` rules-of-hooks) |
| Frontend `next build` | could not be verified in the sandbox — `next/font` needs Google Fonts egress. Please run `npm run build` once locally. |
| `requirements-dev.txt` | `pip install --dry-run` resolves (it did not before — see F-37) |
| Goldens / fingerprints / balance report | rebaselined for phase 3 (see the phase-3 rebaseline section); fingerprints bit-identical across two fresh processes |

---

## F-01 · Reputation: BU stock, derived group figure, zero-baseline contagion

**Files:** `backend/engine.py`

* `calc_contagion` normalises the sigmoid to its severity-0 value, so a crisis of
  severity 0 subtracts exactly 0 (it used to subtract ≈5.9 points every tick — the
  "phantom drift"). Severity 30 still costs ≈16 points, severity 100 ≈50 (the cap).
* `group_reputation` is now derived each tick from the mean BU `reputation_score` minus
  that dip. Every between-tick write to `gs["group_reputation"]` (side tracks, agents,
  black swans, dividend ratchet, emissions breach) is folded into the BU stock on the
  next tick by a stamp-and-carry reconciliation (`reconcile_reputation_stock`, stamp key
  `_group_rep_derived` in `active_event_flags`). Nothing is lost, nothing double-counts.
  An earlier attempt to edit the 13 write sites individually was abandoned for this: one
  mechanism, no site can be missed.
* The emissions-breach penalty now also lands on the BU stock (it only touched the
  group figure before, so it evaporated on the next tick).

**Evidence:** `TestF01ReputationStock` — ten quiet rounds hold the group figure equal to the
BU average (was −5.9/round); a −10 between-tick write shows up as `reputation_carry_applied
= −10` and in every BU. `test_engine.py::test_no_crisis` and
`test_comprehensive.py::test_single_bu` were updated from "≈ avg − 5.9" to "= avg".

## F-02 · Cost of capital: units bug, stock-not-flow base, ratchet re-examined

**Files:** `backend/engine.py`

* `water_dependency` (0–100) is divided by 100 before it reaches
  `calc_esg_adjusted_wacc`, whose `biodiversity_dependency` is a 0–1 fraction. The raw
  mean (54.25) produced a +76-point "nature premium" that pinned WACC at the 20% cap from
  round 1 for every team — and, through the Gordon multiple, the 6× exit-multiple floor for
  every team. Nature premium at seed is now ≈0.0076 (0.76 pp).
* The cost-of-capital *base* is kept as a stock in `active_event_flags.base_cost_of_capital`
  (seeded from the session's starting `cost_of_capital`), with the same stamp-and-carry
  pattern as F-01 (`_coc_derived`) so between-tick writes (tipping-point premium, rate
  spikes) are absorbed. The per-regime macro modifier is therefore applied as a level and no
  longer compounds round over round.
* Ratchet re-examined, not changed: with WACC no longer pinned, the regulatory floor now
  does what its comment says — pure_B climbs 5.2% → 8.0% over ten rounds, and only
  ≥20% investment erodes it.

**Consequence worth reading (MODEL_CARD §2.2, §3.7):** the exit multiple now moves. A
healthy team sits on the 18× ceiling; WACC must exceed ≈7.7% before the multiple falls,
12× ≈ 10.5% WACC. Terminal values in BALANCE_REPORT_BASELINE.md roughly doubled
(aggressive_green $250M → $557M, balanced $123M → $261M); solvency outcomes and the
ordering are unchanged. Whether an 18× ceiling should bind for most teams is a
calibration decision recorded as an open item, not made here.

**Evidence:** `TestF02CostOfCapital` (premium magnitude; base stays 0.05 over seven
self-fed rounds). Golden traces and the two `multi_toggles` treasury fingerprints were
rebaselined; the four `legacy_abc` fingerprints did not move (cost of capital is not a
treasury flow — it reaches treasury only via NCD interest, a BU stock, and the exit
multiple).

## F-03 + F-15 · CBAM rate and store parity

**Files:** `backend/config.py`, `simulation_config.json`, `simulation_config.xlsx` (cell
D98), `backend/database_memory.py`

* `surcharge_rate` 100 000 → **100 $/tCO2e** in both config sources. Because deployed
  volumes load their own copy of the config, `config.py` also clamps any value above
  $5 000/t back to the default with a startup warning — the poison value cannot survive
  on the volume. At seed emissions (~900 t Scope 1+2) a hit is now ≈$90k, not $81–120M.
  Note: at a realistic price the levy is small relative to treasury; a facilitator who
  wants it to bite can raise it in config up to the sanity cap.
* Memory store parity: `fetch_latest_state` and `fetch_round_history` pass every stored BU
  key through (`_BU_EXPLICIT_READ_KEYS` whitelist + `**rest`), mirroring the Postgres
  `risk_factors` pack/unpack. Previously `scope_1_ci`, `supplier_defection_active`,
  `green_premium_squeeze`, … were dropped by the memory store, which is why CBAM (and any
  mechanic reading them next round) fired only in production and never in a test.

**Evidence:** `TestF03Cbam`, `TestF15BuKeyParity` (memory) and
`test_extra_bu_keys_survive_a_round_trip_on_postgres` (PG) pin both stores to the same
BU shape.

## F-20 / F-21 · Tenancy: session list scoped by JWT, ownership on every session route

**Files:** `backend/admin_router.py`, `backend/admin_resources.py`,
`backend/admin_analytics.py`, `backend/admin_teleprompter.py`,
`backend/tests/test_admin_route_guards.py`

* `GET /api/admin/sessions`: scope comes from the signed cookie, not the optional
  `facilitator_id` query parameter (which could be omitted to receive every cohort on the
  platform, roster bcrypt hashes and revealable initial passwords included). Admins see all
  and may still narrow; everyone else sees owned + observed cohorts, whatever the query
  string says. `password` (the hash) is stripped from every roster row; the revealable
  initial credential survives only on rows the caller owns. Same treatment for
  `list_players` and the leaderboard roster.
* 65 tenancy assertions were added to session/cohort-scoped admin routes: `_assert_session_ownership`
  (writes), the new `_assert_session_visible` (reads: owner / co-facilitator / admin) or
  `_assert_player_or_facilitator_can_view` (resources the cockpit *and* the console fetch:
  pacing, R2 BU selection, complexity feed, quiz/consultant flags). Eight routes that had
  no role guard at all received one. `GET /teleprompter/agents/{session_id}` (live agent
  state for any session, no credential) is guarded and tenanted.
* Route-guard ratchet banked: `_MAX_UNTENANTED` 8 → **1** (the residue is the player
  WebSocket, which verifies a signed ticket inline), `_MAX_UNGUARDED` 60 → 58. The
  counter now recognises all four tenancy helpers.

**Evidence:** `TestAuthorizationBoundaries` (memory) and
`test_cross_cohort_facilitator_is_refused_on_postgres` (PG): facilitator B cannot list,
read, pace, roster, rename or bonus cohort A; the owner and admins can.
`probe/security_probe.py` (not part of the patch) shows every probed path closed.

## F-22 · Signed player token; initial password enforced server-side

**Files:** `backend/auth_jwt.py`, `backend/router.py`, `backend/admin_router.py`,
`frontend/app/hooks/useSimulation.js`, `frontend/app/layout.js`, six player components

* Login and join mint a signed, session-scoped `player_token` (HS256, 12 h, claims
  `sid/pid/typ/obs`). Every session-scoped player route (32 GETs plus every write) requires it (`Authorization:
  Bearer` or `X-Player-Token`); the bare `X-Player-Id` header is display-only and a request
  carrying it without a token gets `401 {"code":"player_token_required"}` so the cockpit
  returns to login. A token for another session is 403. Facilitator cookies are admitted on
  player routes only for cohorts they can see (B could previously commit for team A).
  Solo sessions (no roster, no owner) stay UUID-bearer, unchanged.
* A player still on the initial password may read, but every mutating player route is
  refused with `403 {"code":"password_change_required"}` until `/change-password` succeeds
  (roster flag read from the registry or the cohort's `registered_players`). The cockpit
  re-opens the change-password modal on that code instead of showing "round locked".
* Facilitators: `get_fac_role` refuses every admin call except login / change-password /
  refresh / logout while `must_change_password` is set. MASTER_PASSWORD impersonation is
  exempt through a signed `mb` claim on the JWT (consistent with the login response, which
  already reported `must_change_password: false` for those logins); the claim survives
  `/auth/refresh`.
* Frontend: the token is stored at login/join and cleared at logout; a global fetch
  interceptor in `app/layout.js` adds `Authorization` + `X-Player-Id` to every
  `/api/simulations` and `/api/admin` call (the ~50 individual fetch sites did not need
  touching); 401 `player_token_required` in the dashboard fetch and the poller routes back
  to login.
* Test support: `conftest.rotate_facilitator_password`, `player_login`,
  `player_token_headers`. Fourteen existing test files that logged in with initial
  credentials or forged `X-Player-Id` were adapted.

**Evidence:** `test_player_identity_is_the_signed_token_not_the_header`,
`test_default_password_can_only_change_itself`,
`test_facilitator_default_password_can_only_change_itself`,
`test_master_password_impersonation_is_exempt_from_the_first_login_gate`;
`test_player_token_and_first_login_gate_on_postgres`.

## F-24 (hardening the same paths exposed)

* `/set-username` was fully unauthenticated (rename any player or facilitator; probe which
  ids exist). Now: a player renames only the identity its token carries; a facilitator
  renames itself, or players in cohorts it can see; admins anyone; solo sessions by UUID.
  (My first version of this shadowed the module-level `db` name and would have 500'd the
  solo path — caught by the new test, fixed.)
* `/change-password` had no rate limit (a password oracle). It now shares the
  `player_login` limiter per identity and per IP.

## F-26 · Simultaneous commits exhaust the pool

**Files:** `backend/config.py`, `backend/router.py`, `backend/main.py`

**Correction to the audit's characterisation.** The report said 40+ simultaneous commits
"hung >90 s with zero 503s". Re-instrumenting the probe shows what actually happens:
each commit holds one pooled connection for its advisory lock while its queries need a
second; at 40 in flight (= `DB_MAX_CONNECTIONS`) every commit waits for a connection none
will release, and after `DB_ACQUIRE_TIMEOUT_SECONDS` (10 s) **39 fail with an unhandled
`asyncio.TimeoutError` (HTTP 500) and 1 gets a 503 — zero succeed.** The probe's
`except asyncio.TimeoutError` caught the app's own exception and printed "HUNG". The
severity stands (a whole round's commits rejected for everyone, students see "internal
server error"), the mechanism is a 10-second failure, not a hang.

* **Commit gate:** a per-worker `asyncio.Semaphore` bounds in-flight commits to
  `COMMIT_MAX_IN_FLIGHT` (default `DB_MAX_CONNECTIONS // 2 − 1` = 19), so every admitted
  commit can always obtain its second connection and two are left for polls. Excess
  commits queue in arrival order; only a wait longer than `COMMIT_QUEUE_TIMEOUT_SECONDS`
  (45 s) fails, with `503 {"code":"commit_queue_full"}` + `Retry-After: 5`. The
  per-session lock still fails a *second commit for the same team* fast with 409. Applied
  to both the HTTP commit and the auto-commit path.
* **Pool timeouts are 503, not 500:** an `asyncio.TimeoutError` escaping a handler is
  answered `503 {"code":"server_busy"}` + `Retry-After` by a dedicated exception handler.
* **Cockpit:** 503 on commit is auto-retried like 429 (honours `Retry-After`, max 2), with
  a message that says nothing was lost.

**Evidence (`probe/pg_deadlock_probe.py`, real Postgres, pool 40):**

| simultaneous R1 commits | before | after |
|---|---|---|
| 30 | all 201 in 0.9 s | all 201 in 0.9 s |
| 40 | 0 succeed (39×500 after 10 s, 1×503) | **all 201 in 1.1 s** |
| 60 | — | **all 201 in 1.4 s** |
| 150 (= 30 cohorts × 5 teams at one deadline) | — | **all 201 in 3.4 s** |

`TestF26CommitGate` pins: 12 commits through a gate of 3 all succeed with ≤3 ever in
the engine; a queue wait beyond patience is a retryable 503; a pool timeout is 503 not 500;
gate × 2 ≤ pool.

## F-27 · Dashboard polling cost

**Files:** `backend/database.py`, `backend/database_memory.py`, `backend/router.py`,
`backend/main.py`, `frontend/app/hooks/useSimulation.js`

* **Poller asks for what it lacks:** `?since_round=<highest round held + 1>`. The latest
  `global_state` + `business_units` always come back (that is what the badges and the
  round-advance check read); `history` is empty unless the server moved on, in which case
  it holds exactly the new round(s) and is merged into state by round number. The filter
  now runs in the store (SQL `round_number >= $2`), not in Python after fetching the game.
* **3 queries instead of 1 + 2×rounds:** `fetch_round_history` fetches the BU rows and the
  decision rows for all selected rounds with `= ANY($1)` and groups in Python.
* **One sibling scan per poll:** `_cohort_sibling_rounds` → new `db.fetch_latest_rounds
  (ids)` (one `GROUP BY` query) feeds both the commit badge and the free-advance status,
  which used to each query every sibling.
* **GZip** (`GZipMiddleware`, min 1 KB, level 5) — transparent to every client.
* **Slimmer body:** engine-internal `_prev_global_states` (~25 KB, the momentum window)
  is stripped from every response `active_event_flags`; `consequence_dna_snapshot` (~19 KB,
  served by its own endpoint, read by the Scorecard from the latest state only) from history
  entries. New dicts are built — the stores are not mutated.

**Evidence (`probe/payload_probe2.py` memory store; `probe/pg_load_probe.py` Postgres):**

| | before | after |
|---|---|---|
| Full dashboard at R10 (decompressed / wire) | 1 057 KB / 1 057 KB | 897 KB / 214 KB |
| **Poller request at R10** (decompressed / wire) | 1 057 KB / 1 057 KB | **≈130–240 KB / 30–58 KB** |
| Poller request, one worker, PG, 120 concurrent | ~18 req/s (full body) | **58 req/s** |
| Full dashboard, one worker, PG, 120 concurrent | ~18 req/s | 12–16 req/s (gzip CPU on a 900 KB body; now fetched once per round, not every 5 s) |
| Egress for 150 cockpits polling every 5 s at R10 | ≈30 MB/s | ≈1–1.7 MB/s |

`TestF27DashboardPayload` pins the `since_round` contract, the stripped keys (and that the
store still holds them), gzip on large bodies only, the batched store helpers and that a
cohort dashboard performs exactly one sibling scan.
`test_dashboard_history_batched_queries_and_since_round_on_postgres` pins the PG path.
Remaining per-poll weight is the latest state's own flags (`balance_sheet`,
`npc_stakeholders`, engine sub-states) which the cockpit reads; left as is.

## F-37 · CI never ran

**File:** `backend/requirements-dev.txt`

`pytest==8.3.4` conflicts with `pytest-asyncio==1.4.0` (requires `pytest>=8.4,<10`), so
`pip install -r requirements-dev.txt` failed on the resolver and **both** backend CI jobs
died at the install step. Pinned `pytest==8.4.2`; `pip install --dry-run` resolves. The
PG parity job's file list is unchanged; `test_postgres_parity.py` itself gained the
tenancy, token, BU-parity and batched-history cases so the production store is covered.

## F-40 · NEW, Critical · Player ids were only unique within a cohort

Found while running the new PG parity tests against a database holding earlier probe
cohorts: a freshly minted player could not log in ("Incorrect password") because another
cohort had the same id.

**Where:** `database.generate_player_id` / `database_memory.generate_player_id` drew
`MUR-XXX` (17 576 values) unique only against the cohort's own `allowed_player_ids`;
`admin_router` bulk-upload and induct paths used `_next_player_id`, an in-process counter
that **restarts at MUR-001 on every deploy**, so every cohort rostered after a restart
re-issued MUR-001, MUR-002, …. `player_login` resolves an id platform-wide (first registry
or roster match) and the default password is derived from the id (`MUR-001@123`).

**Failure scenario:** cohort B's team MUR-001 signs in with its default credential and is
placed in **cohort A's** MUR-001 game (whichever record is found first) — another team's
decisions, results and roster; or, once team A has personalised its password, team B is
told its password is wrong and cannot play. For 150 random-letter ids the birthday bound is
≈47 % that at least one pair collides; for sequential ids after any redeploy it is certain.

**Fix:**
* `db.player_id_in_use(pid)` / `db.list_all_player_ids()` in both stores (PG: one
  indexed JSONB query over `sessions.metadata` — sub-session `player_id`,
  `allowed_player_ids`, `registered_players`; deleted cohorts included so an id is never
  reissued).
* Random ids: draw until unused platform-wide. Sequential ids (`MUR-NNN` from bulk upload
  and induct, `P-NNN` from `/players/register`): `_mint_sequential_player_id(prefix)` seeds
  the counter once per process from every id the store and the registry have issued and
  still checks each candidate against the store (multi-worker safe). `DELETE /players`
  re-seeds instead of resetting to 1.
* Legacy collisions already in a live database: `player_login` collects every candidate
  record and picks the one whose password verifies; the join path prefers the record
  belonging to the cohort being joined. If two records share both id and password the login
  is refused with `409 {"code":"player_id_ambiguous"}` (a coin toss between two teams' games
  is the one thing it must not do) and the facilitator reissues one id.

**Evidence:** `TestF40PlayerIdUniqueness` — a rigged random draw cannot reissue another
cohort's id; a "redeployed" counter continues past every issued id (roster and register
paths); a legacy collision resolves by password to the right cohort; an ambiguous one is
refused. `test_player_ids_are_unique_across_cohorts_on_postgres` pins the JSONB lookup and
both mint paths on the production store.

**Id width widened in the same branch:** random ids are now `MUR-` + four letters
(`config.PLAYER_ID_RANDOM_LETTERS`, default 4, env-overridable 3–8): 456 976 ids instead of
17 576, since ids are never reissued for the platform's lifetime. Existing three-letter ids
stay valid — nothing validates the width and the uniqueness check covers both
(`test_random_ids_are_four_letters_and_old_three_letter_ids_still_work`). Roster ids
minted by bulk upload / induct keep the `MUR-NNN` form.

---

## Rebaselines in this change (each deliberate, each caused by F-01/F-02)

* `backend/tests/golden/financial_trace.json`, `stakeholder_slo_trace.json`
  (`MURESSONS_REBASELINE_GOLDEN=1`): `cost_of_capital` 0.20 → 0.05 at R1; group
  reputation in a permanent severity-40 scenario 26.96 → 29.26 (normalised sigmoid).
* `test_treasury_waterfall.py`: the two `multi_toggles` fingerprints; verified
  bit-identical across two fresh processes before pinning; `legacy_abc` unchanged.
* `BALANCE_REPORT_BASELINE.md` (`scripts/balance_report.py --write`): terminal values
  ≈2× (exit multiple off the 6× floor); bankruptcies and ordering unchanged.
* `MODEL_CARD.md`: §2.1 CBAM row, §2.2 exit multiple + cost of capital rewritten to the
  measured behaviour, new §2.6 reputation, §3.7 terminal-value shift, §5 change log.

---

# Phase 3 — "Should change soon" and "Can wait" (items 9–18)

Design decisions taken from the review conversation: **F-05** debit treasury and amortise
the loan; **F-32** remove Extended Horizon; **F-31** defer multi-worker, keep the single
worker; **F-11** default F2 continuous pressure OFF.

## F-04 · Flow penalties made transient — and F-04b, the cash they must still cost

Four more per-round penalties no longer compound into the persisted BU base: the
supply-chain contagion OPEX surcharge (`engine.py` FEATURE 8), the DSO deferral (FEATURE
23 — the deferred cash was already scheduled back into treasury next round, so shrinking
the revenue base as well double-charged a timing effect), supplier defection and the
green-premium squeeze (reporting layer). Each uses the existing `ctx.record_transient`
mechanism (rulings A/C). Inflation is applied after some transients are recorded, which
multiplied their footprint and leaked `delta × inflation` into the base every round; the
new `ctx.scale_transients(field, factor)` keeps the additive reversal exact
(`test_inflation_after_transients_leaves_no_residual`).

**F-04b (found while rebaselining).** The treasury is banked in the financial layer
(`new_treasury = base + CSF − …`). A transient recorded *after* that line — the talent
retention premium and NCD OPEX penalty (rulings A/C, already in HEAD) and now defection
and squeeze — had already missed this round's P&L, and its end-of-tick reversal meant it
never reached next round's either. Those penalties were narrative only; the proof was the
treasury fingerprints, where `multi_toggles` had collapsed onto `legacy_abc` bit-for-bit.
`TickContext.csf_banked` is set at the banking line; `record_transient` after it charges
`new_treasury` directly, accumulates `post_csf_flow_cash`, events
`post_csf_flow_adjustments_cash` and writes a waterfall entry ("Flow surcharges after
gross profit"); the treasury-ledger conservation law gained the term and closes to 0.00
on every round of every runner case
(`TestF04FlowPenaltiesAreTransient::test_post_csf_transients_still_cost_cash_this_round`).

## F-05 / F-06 · CapEx leaves the treasury; synergy saving capped

`engine.py` CapEx block: the tranche inside the allowance (`max(0, treasury) ×
FINANCIAL_FREE_CSF_PCT`, floored at `CSF_POOL_FLOOR`) is paid in cash this round
(`capex_equity_funded`); the excess is drawn as a term loan (`capex_loan_drawn`) into the
`capex_loan_balance` stock in `active_event_flags`, with interest on the opening balance
(`loan_interest_payment`, `FINANCIAL_DEFAULT_LOAN_RATE` 12%) and straight-line repayment
over the remaining rounds (`capex_loan_repayment`; bullet at R10). Waterfall entries
"CapEx (cash-funded)", "Loan Principal Repayment", "Loan Interest"; `balance_sheet.py`
carries `capex_term_loan` inside covenant `total_debt` and the term-loan interest in the
income statement; the R10 finale's net debt includes the balance. Negative-treasury
clamps stop CapEx from ever *crediting* treasury. `RoundLedger` gained
`capex_equity_funded` / `capex_loan_repayment` and the conservation law both terms.
Tests: `TestF05CapexFinancing` (allowance, loan draw and amortisation, R10 repayment,
balance sheet).

`calc_synergy_opex`: `captured = min(1, √ratio × SYNERGY_DAMPENING_FACTOR × synergy)`,
`factor = 1 − SYNERGY_MAX_REDUCTION_PER_ROUND × captured` (0.06, new config key
`synergy.max_reduction_per_round`, xlsx row 47). `TestF06SynergyCap`; `test_engine.py` /
`test_comprehensive.py` synergy expectations updated.

## F-07 · Engine parameters derived server-side

`router.py::_commit_turn_impl`: `crisis_severity = base_crisis_severity_for_round(round)`
(new helper in `round_logic.py`, reads `special_rules.base_crisis_severity`, 0 for rounds
without one), `imitation_decay_rate = DEFAULT_IMITATION_DECAY_RATE` (new config key
`imitation_decay.default_rate` 0.05), `emergency_credit_used = treasury × CSF fraction <
CSF floor`. The body fields are still accepted for older clients but ignored (logged when
they differ). Same for the shadow tick and the side-track commit (`base_track.py` gained
`base_crisis_severity = 40.0`). `models.py` documents the fields as ignored; `page.js` and
`SideTrackPanel.js` no longer send them (the `emergencyCreditActive` memo is gone).
`TestF07ServerDerivedParameters`.

**`dry_run.py` (balance runner) fixed to match.** It passed `crisis_severity=40.0` into
*every* round — a permanent crisis production never had (the client sent 0; pre_tick
overrides only the R4 crisis round to 40). With the contagion dip that is ≈31 reputation
points a round; group reputation hit 0 by R4 in every scripted run and the talent premium
ran at its maximum. Under the old transient rule that premium cost nothing, so the report
looked fine; with F-04b it bankrupted every strategy — which is how the harness bug
surfaced. The runner now uses the same three server-derived values as the router.

## F-08 / F-09 / F-10 / F-12 / F-13 · Dead or positional mechanics

* **F-08** stakeholder fatigue compared the derived group figure with the BU mean — a gap
  that is identically ≤ 0 — and never fired (0/24 probe combinations). It now dampens
  each BU's reputation *gain* this tick relative to `ctx.rep_at_tick_start`, before
  contagion; losses are never dampened.
* **F-09** the positional rule giving every `option_a` −3 CI and every `option_c` +2 CI is
  removed; options carry their configured `carbon_intensity_delta`. (It contradicted the
  configs — R1-A "Surface-Level Scan" is +2 in config and got −3 — and drove a
  pharma/electronics conglomerate to 0.0 CI, zeroing its R10 carbon tax.)
* **F-10** the NCD OPEX penalty was `ncd × 50,000 / 1e6` = five cents per index unit;
  now `NCD_OPEX_PENALTY_PER_UNIT` $1,000 (config key `ncd_parameters.opex_penalty_per_unit`,
  xlsx rows 25–27; thresholds 5,000 / 1,000 on the index's real scale, with a legacy-value
  guard for volume copies of the config). SDG 6 / 14 thresholds were 0.4 / 0.3 against a
  0–100 `water_dependency` — unreachable; now 40 / 30.
* **F-12** one terminal-value formula: the BRSR finale path now applies the same EBITDA
  floor and M_SDG as the main path (`ebitda_for_tv = max(EBITDA_FLOOR, terminal_ebitda)`,
  `× m_sdg`); `calculate_mr` is the single M_R arbiter.
* **F-13** `ci_baseline_r1` was read by the SBTi pathway but never written, so every BU was
  "off track" from R2; it is stamped from the pre-decision CI the first time a BU is seen
  (both stores persist extra BU keys, F-15).

Tests: `TestF08…TestF13` classes.

## F-11 · F2 continuous NPC pressure default OFF

`pedagogical_engine.py` `stakeholder_slo_feedback_enabled: False`; `test_stakeholder_defaults`
and `test_stakeholder_golden_trace::test_toggles_default_off` pin it; EVAL_Stakeholder_SLO
row updated. **Measured:** with the toggle ON the disciplined bot (aggressive_green) ends at
M_R 1.03 / $572M / FRAGILE_GIANT; OFF it reaches M_R 1.43 / $891M / SAFE_HAVEN — the ≥ 1.2
the MODEL_CARD promises a disciplined team. Nothing else in the report moves between the two
settings (balanced 1.03, pure_B 0.92 either way).

## F-16 / F-17 / F-18 · One valuation story across the cockpit

The engine emits a `valuation_preview` event each round (`wacc`, `exit_multiple`,
`mr_projection`, `ebitda`, `ev_estimate`, `note`) using the same Gordon multiple and
`calculate_mr` the finale uses. `RoundBriefing.js` shows `ev_estimate`; `MarketTicker.js`,
`AnnualReport.js`, `GameOverSummary.js` (fallback 17×, not 12×) and
`stockValuationEngine.js` take `exit_multiple` from the server (NCD cap 0.6 at NCD/4000);
the trading-floor rival uses the median team multiple; `TechnicalGlossary.js` M_R and
circularity entries match the backend formulas; SIMULATION_CONTEXT seed table, the R9
strike probability (50%, matching `round_configs.py`), and the VRIO decay (5%) corrected.

## F-19 / F-36 · Failures are visible

`round_logic.py::_engine_failed(extra, engine, exc)` replaces 22 `print("[WARN] … failed")`
sites: logs at ERROR with traceback and records into `events["engine_failures"]`; the
router adds `engine_failure_alert` to the commit response, broadcasts
`{"type": "engine_failure"}` on the admin socket, and counts into `_ENGINE_FAILURE_COUNTER`
→ `/health` `engine_failures`. `admin_shared.record_persistence_failure` /
`persistence_health()` do the same for snapshot / registry writes (strict health goes
degraded). Swallowed exceptions on the critical path (seed_effective_flags, hidden
resources, sentiment, ban-save) are recorded instead of passed.

**F-41 (found by F-36's logging).** `stakeholder_sentiment.py` never defined
`initialise_sentiment` / `update_stakeholder_sentiment`; the import failed on every
commit and was swallowed, so the stakeholder-sentiment engine had never run in
production. Both functions are implemented (`TestF19VisibleFailures` exercises the
visibility; two full 10-round games, legacy_abc and advanced_climate, commit with an
empty `engine_failures`).

## F-23 / F-24 · Remaining guards

`set_esg_profile_weights` → `require_super_admin` (was facilitator); `esg_weights` removed
from the facilitator `ROLE_ALLOWED_TABS`, `sidebarConfig.js` `requiredRole: 'super_admin'`,
`ESGWeightsEditor.js` header. `admin_analytics.get_cohort_analytics_visibility` and
`admin_teleprompter` `/teleprompter/agents/{session_id}` gained facilitator guards plus
`_assert_session_visible` (anonymous callers passed through). `/set-username` is
facilitator-scoped via `_assert_session_visible`. Route-guard ratchets 58/1.

## F-28 / F-29 / F-30 / F-31 · Scalability

* **F-28** `get_child_sessions` filters in SQL and `fetch_child_session_ids` /
  `fetch_latest_rounds` / `fetch_round_history(since_round)` are batched (3 queries, not
  N); JSONB expression indexes `idx_sessions_parent_cohort`, `idx_sessions_player_id`
  (`CREATE INDEX IF NOT EXISTS` at startup). Shockwave, messages, undo, relock, pacing and
  dashboard sibling scans use them (`TestF28IndexedSiblingLookups`, `TestF27…`).
* **F-29** the memory store's JSON snapshot is debounced (one write after a quiet window,
  `MURESSONS_SNAPSHOT_DEBOUNCE_MS`, default 500) and written off the event loop;
  `flush_snapshot()` at shutdown (a parity no-op exists on the Postgres module so
  `db.flush_snapshot()` is safe on either backend). `conftest.py` sets the debounce to 0
  for tests.
* **F-30** bcrypt verify/hash/upgrade and the credential mints have `_async` variants on
  the thread pool; every request-path caller uses them (`test_default_credentials` pins
  it); openpyxl workbook builds run via `asyncio.to_thread`.
* **F-31** deferred by decision: single worker stays; `/health` `scaling` reports the
  gate settings so the constraint is visible.

## F-32 / F-33 / F-34 / F-35 · Round-flow correctness

* **F-32** Extended Horizon removed: `POST …/extend` → 410 `extended_horizon_removed`;
  `branching_engine.py` EXTENDED_ROUNDS / `get_extended_round_config` /
  `is_extended_mode_available` deleted; `test_extended_horizon.py` now pins the 410.
* **F-33** `_auto_commit_request` builds the default `option_b` in *display* space via
  `get_shuffle_mapping(seed, round)["canonical_to_display"]` — the auto-commit used to
  submit the canonical key into a shuffled round and land on a random option.
* **F-34** `unlock_next_round` is idempotent: `target_round` in the body, capped at
  `SIM_ROUNDS`, returns `already_unlocked` / `max_round`; `RoundPacingControl.js` sends
  the target (`TestF34IdempotentUnlock`).
* **F-35** a commit with no strategic option is a 400 `choice_required` instead of a
  silent default (`TestF35ChoiceRequired`).

## F-38 / F-39 · Cruft

`_calc_rw_avg_ci` is an alias of `calc_revenue_weighted_avg_ci`; `check_bu_greenwash_scandal`
references removed from `blueprint.md`; `backend/test_e2e_full_flow.py` deleted (superseded
by the collected `tests/test_full_run_e2e.py`, which says so); `backend/test_e2e_multiplayer.py`
and `test_shadow_board_e2e.py` moved to `scripts/harness/` without the `test_` prefix (they are
`__main__` harnesses that collected zero tests; the shadow-board one never imported
`requests` nor defined its base URL — fixed so it runs); `revert.py` and `scratch/` (8 page
JPEGs) deleted (`revert.py` restored from a `temp_archive` that was never in the repo;
`SAFETY_MANIFEST.txt` says so now); the 19 `print()` sites in `admin_router.py` use the
module logger (`database_memory.py`'s persistence prints are left — a test asserts them on
stdout); unused frontend deps `@dnd-kit/sortable`, `@dnd-kit/utilities` (transitive of
`@dnd-kit/core`, still installed) and `styled-jsx` (Next ships its own nested copy) removed
from `package.json` with the lockfile refreshed (`npm install --package-lock-only`); stale
doc statements listed under F-39 corrected in MODEL_CARD, SIMULATION_CONTEXT,
EVAL_Stakeholder_SLO, the glossary and `models.py`.

## Rebaselines in phase 3 (each deliberate)

* `backend/tests/golden/financial_trace.json`, `stakeholder_slo_trace.json` — every
  trajectory moved (CapEx now leaves treasury; flow penalties reach cash; synergy cap).
* `test_treasury_waterfall.py` — all six fingerprints; note above the table records why;
  bit-identical across two fresh processes. The conservation law has two new terms
  (F-05) plus `post_csf_flows` (F-04b) and closes to 0.00 on every round.
* `BALANCE_REPORT_BASELINE.md` — regenerated with the fixed runner. Strategy outcomes:
  aggressive_green $891M / M_R 1.43 / SAFE_HAVEN, balanced $415M / 1.03, pure_B $148M /
  0.92 (all solvent); pure_A / pure_C / extractive bankrupt at R7. No dead levers.
* `MODEL_CARD.md` §2.2 CapEx, §2.3 (three new rows), §3.1, §3.4, §3.7, §5.

## Config keys the deployed volume must pick up (phase 2 + 3)

The server loads `simulation_config.json` from the durable data dir, so the repo copy is
not what production reads. Update the volume copy (or re-upload the xlsx) for:
`cbam.surcharge_rate` 100; `ncd_parameters.hostile_threshold` 5000,
`ncd_parameters.warning_threshold` 1000, `ncd_parameters.opex_penalty_per_unit` 1000 (the
legacy `opex_scaling_factor` key is ignored with a warning); `regulatory_ratchet.baseline`
20; `synergy.max_reduction_per_round` 0.06; `imitation_decay.default_rate` 0.05.
`config.py` clamps the two known poison values (CBAM > 5,000/t, NCD thresholds > 100,000)
back to defaults with a warning, so a stale volume degrades loudly rather than silently.

## Things to know before merging

1. **Observable behaviour changes for users:** facilitators on an initial password can only
   change it; players on an initial password can look but not commit; a stale cockpit
   (pre-deploy tab) will get 401 and be sent to login once. Terminal values are ≈2× the
   previous baseline — re-read any rubric that quotes absolute TV bands.
2. **Config on the deployed volume:** `simulation_config.json` there still says 100 000 for
   CBAM; the startup clamp neutralises it, but update the volume copy too.
3. **Env knobs added:** `COMMIT_MAX_IN_FLIGHT`, `COMMIT_QUEUE_TIMEOUT_SECONDS`,
   `PLAYER_TOKEN_TTL_HOURS` (12 h — long enough for a workshop day; a token expiring
   mid-class means one re-login), `PLAYER_ID_RANDOM_LETTERS` (4).
4. **Test harness note:** the memory-only test modules build a module-level `TestClient`
   and cannot run on Postgres (asyncpg pool bound to a dead loop) — that is why the PG job
   runs a curated list. `test_sec3_session_ownership.py` no longer calls the db module
   directly, but still belongs to the memory job for that reason.
5. `probe/` and `out/` are audit tooling and are **not** in this patch.
6. **Phase 3 behaviour changes players will feel:** CapEx now costs cash (allowance in
   the round, the rest amortised), so treasuries are lower than any pre-change run of the
   same choices; the four post-gross-profit penalties now bite; `/extend` is gone; a commit
   without a strategic option is refused; the auto-commit default lands on the *displayed*
   option B. Terminal values moved again (see MODEL_CARD §3.7).
7. **Files moved/deleted in phase 3** (`git status` shows them as renames/deletions on the
   branch): `backend/test_e2e_full_flow.py` (deleted), `backend/test_e2e_multiplayer.py` →
   `scripts/harness/e2e_multiplayer.py`, `backend/test_shadow_board_e2e.py` →
   `scripts/harness/shadow_board_e2e.py`, `revert.py` and `scratch/` (deleted).
