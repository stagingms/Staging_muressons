# Implementation — UX Audit build, 2 Aug 2026

Companion to `AUDIT_UX_Product_2026-08-02.md`. Everything below is UI-layer or
additive; the simulation engine (`engine.py`, `round_logic.py`,
`terminal_valuation.py`, …) is untouched. Verified against the full backend
suite: **1785 passed, 6 skipped** (only `test_deploy_image_hygiene.py` was not
run here — it reads `.dockerignore`/`Dockerfile`, which were absent from the
review sandbox and are unmodified).

## What shipped

### Control room ("the facilitator should not be running it blind")
- **§7.1 — Manual-mode advance fixed.** `RoundPacingControl.js` now calls the
  real endpoint `/api/admin/sessions/{id}/pacing/unlock` (was `/unlock-next`,
  which never existed — every Manual advance 404ed). Adds `credentials`,
  specific 403/error copy, and a disabled state at Round 10.
- **§7.6 — Confirm + inverse on advance.** Unlock and Force Advance now use the
  app's `ConfirmModal` with live blast radius ("2 of 5 players have committed
  Round 4…"). New backend endpoint `POST /sessions/{id}/pacing/relock`
  (`admin_router.py`, tag RL-1) — one-field inverse of unlock, floored at the
  highest committed round (409s with a pointer to Undo Round if a player already
  committed into it). Surfaced as a 60-second "↩ Undo — Relock Round N" button
  after each unlock.
- **§7.2 / §9 — Run Bar.** New `components/RunBar.js`, mounted persistently in
  `admin/facilitator/page.js` whenever a cohort is selected: round, ●●○○ commit
  tally, auto-commit count, divergence warning (R2–R4 split), pacing mode +
  next unlock, backend health + data freshness, one-click Advance (manual mode,
  confirmed), links to Pacing and the Projector.
- **§7.2 — cohort-pulse extended** (`admin_router.py`, tag RB-2): response now
  carries `commit_progress {target_round, committed_count, total_players,
  min_round, diverged, auto_committed_count}`, `pacing {mode, unlocked_round,
  next_unlock_at}`, and per-team `committed / has_saved_draft /
  auto_committed_last_round / is_cohort_shell / player_id`. Same rule as the
  players' own badge (`router._cohort_commit_progress`), so both surfaces
  always agree. `CohortPulse.js` renders ✓/◐/○ per player + a header tally.
- **§7.3 — restart-safe roster** (`router.py` tag RB-1 + `main.py`):
  `rebuild_session_players()` reconstructs the cohort→players map from the
  durable store via the parity API (memory AND Postgres), called at startup and
  as a throttled (30 s) self-heal inside `_cohort_commit_progress` and
  `_auto_commit_laggards`. Verified: after a simulated restart, the X/Y badge
  returns (2/2) and Force Advance actually advances stragglers.

### Player-side fixes
- **§7.4 — validate before confirm.** `page.js` `preflightCommit()` runs the
  full gate set (side-track, R1 stakeholder map, R2 materiality, quiz,
  decision, allocation) BEFORE the review modal opens (`onPreflight` prop into
  `ExecutiveCockpit`); `attemptCommitTurn` keeps the same checks as a backstop.
  Modal buttons renamed: "← Go back / Commit without predicting / ✓ Commit
  decisions" — the escape hatch no longer shares copy shape with a commit.
- **#5 — honest in-flight state.** The 800 ms "Processing Decision…" ceremony
  previously ran BEFORE the network request. It is now bound to the actual
  request lifetime (minimum 800 ms hold) and cleared in `finally`.
- **§7.8 — auto-commit disclosure** (tag AC-1/AC-2). Server: both auto-commit
  paths now stamp `auto_committed_source` (`"draft"` vs `"default"`) into
  `active_event_flags` (metadata written after the engine ran — never read by
  it). Client: a persistent caution card in the cockpit ("⏱ This round was
  submitted for you… Option B, $1 to each business unit") replaces the
  5-second toast as the durable notice; the facilitator sees the count in the
  Run Bar and per-player `auto` chips in CohortPulse.
- **#8 — keyboard-operable decisions** (A11Y-2). The two inline legacy A/B/C
  tile renders in `ExecutiveCockpit.js` gained `role="button"`, `tabIndex`,
  `aria-pressed` and Enter/Space handlers (matching `DecisionTile.js`, which
  was already correct).
- **#10 — objective + persisted onboarding** (OBJ-1/OB-1). Round 1 briefing now
  states the scored objective (Terminal Valuation + M_R) above "Begin
  Simulation"; the tour's welcome step names it too; tour completion persists
  per session (`mur_tour_done_<sessionId>`) so a refresh no longer replays it.
- **§7.7 — team fiction retired** (TF-1/2/3). "Waiting for Other Teams" →
  "Players"; "X/Y teams committed" → "players"; CohortPulse relabelled; dead
  "REMEMBER STATION" checkbox removed from the join screen and replaced with
  "One login per person — you run your own company." The client no longer sends
  the fabricated `team_consensus: 'majority'` (NOTE: the backend model still
  defaults the column to `'majority'` — a NOT NULL enum in Postgres; making it
  truly null needs a schema migration, tracked below).

### World-class package (§9)
- **Predictions persist server-side** (PRED-1/2). New player endpoint
  `POST /api/simulations/{id}/prediction` stores per-round prediction text in
  session METADATA (never round state; engine and golden trace untouched). The
  predict-modal now fires it alongside the existing sessionStorage copy.
- **The debrief writes itself** (DN-1). New `backend/admin_debrief_narrative.py`
  (`GET /api/admin/debrief-narrative/{cohort_id}`, `require_sim_manager` +
  ownership) aggregates: final ranking, divergence round (max treasury spread),
  per-player turning points, predicted-vs-actual, auto-committed rounds flagged
  for grading. New `components/DebriefNarrative.js` renders it as read-aloud
  cards, each with a "⛶ Project" fullscreen mode (≥28 px type, Escape/✕,
  dialog semantics). New sidebar tab `debrief_narrative` (Analytics &
  Assessment; added to `ROLE_ALLOWED_TABS.facilitator` in `admin_shared.py`).
- **Projector board** (PJ-1). New `admin/projector/page.js` — room-screen view:
  150 px ROUND numeral, filled/hollow commit dots, "X of Y committed" ≥40 px,
  next-unlock countdown, divergence banner, top-5 table, rotating events
  footer, LIVE/STALE stamp; ≥7:1 contrast, colour never alone. Linked from the
  sidebar ("Projector Board ↗") and the Run Bar.

### Hygiene
- **#11** (A11Y-1): light-theme `--kpi-good/--kpi-warn/--kpi-danger`,
  `--gauge-*`, `--accent-cyan/--accent-gold` deepened one shade — all now
  measured ≥4.5:1 on every light surface (values and ratios inline in
  `globals.css`).
- **#16a** (VIS-1): the 10 inert visibility toggles removed from
  `analyticsRegistry.js` (only `cohort_pulse` had a consumer).
- **#17** (TT-1): three lying tooltips corrected in `sidebarConfig.js`
  (player connection status, generic KPI overrides, PDF export).

## Files touched
Backend: `router.py`, `admin_router.py`, `main.py`, `admin_shared.py`,
`admin_debrief_narrative.py` (new).
Frontend: `page.js`, `admin/facilitator/page.js`, `admin/projector/page.js`
(new), `components/{RunBar (new), DebriefNarrative (new), RoundPacingControl,
CohortPulse, ExecutiveCockpit, RoundBriefing, OnboardingWalkthrough,
JoinCohortModal}.js`, `config/{sidebarConfig, analyticsRegistry}.js`,
`globals.css`.

## Verification performed
- `pytest backend/tests/` (minus deploy-image-hygiene, see above): 1785 passed
  — includes the golden trace, simulation-integrity bounds, commit-race,
  pacing, MP-commit-indicator and role-hierarchy tripwires, all unmodified.
- Ad-hoc functional checks (memory mode): RB-1 restart self-heal (roster map
  cleared → badge returns 2/2, throttle honoured); RB-2 pulse response shape;
  RL-1 relock decrements 3→2→1 and 409s at the floor.
- Every touched/new JS file parses clean under esbuild (JSX loader).
- Not run here: `next build` and the Jest suite (no `node_modules` in the
  review sandbox). **Run `npm run build` (or `npx next build`) in `frontend/`
  once before the next class** — expected clean, but that is the remaining
  gate this sandbox could not execute.

## Deliberately NOT done (needs your decision or a migration)
1. `team_consensus` DB column is still NOT NULL DEFAULT 'majority' — nulling it
   is a Postgres migration + memory-store change.
2. Co-facilitator read-only accounts (#22) — needs an ownership-model decision
   (observer list on the session vs a new role).
3. Shared dialog primitive sweep across the 6 non-compliant modals (#18) — the
   WCAG workstream; `ConfirmModal` is the template.
4. Live-round sidebar mode (#13), cohort-creation wizard (#19), token
   consolidation (#20), full consequence-chain coverage (#21).
5. Default pacing mode is still `'free'` in `RoundPacingControl.js:60` — I did
   not change it because the pacing default also lives server-side
   (`admin_shared._get_pacing`); flipping both to `manual` is a 2-line change
   once you confirm you want Manual as the default for every new cohort.
