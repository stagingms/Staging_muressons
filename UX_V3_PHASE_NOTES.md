# UX v3 — Phase Implementation Notes & Test Evidence

Branch: `ux/v3-phases`. Baseline: `UX_V3_S0_BASELINE.md` (pytest 976 green,
player smoke incl. the expected R2-commit 429, endpoint contract of 303 call
sites, shockwave/bell/rehearsal payload capture).

| Commit | Phase | Contents |
|---|---|---|
| `ec908f9` | S0 | v3 review document |
| `435fa52` | S0 | Baseline evidence + endpoint contract |
| `cd26682` | S1 | Chrome truth & routing hygiene — G-2, G-4, F-5, F-8, F-9, G-5 |
| `924247a` | S2 | Feedback completeness — F-3(b)(c), F-4, G-1 |
| `189097c` | S3-A | F-1 shockwave targeting + impact-preview confirm; G-3 catalog + tripwire test |
| `d12ffb2` | S3-B | F-3a ring-bell tier-2 confirm (all-cohorts truth) |
| `8c9f799` | S3-C | F-6 unified CreateCohortModal role resolution + project_admin branch |
| `f9f7ae5` | S3 | Phase notes + gate evidence |
| `071ef56` | S4 | F-2 rehearsal mode surfaced — the one new request variant, live-proven a no-op |
| `b49cd13` | S5-1 | F-7 create-cohort button truth (frontend-only) |
| `a3bfa83` | S5-2 | G-3 proper — shockwave catalog endpoint (+2 tests) |
| `beda7b0` | S5-3 | F-4 proper — bulk-upload preview endpoint (+3 tests) |

---

## Phase S1 — what changed (rendering/navigation only; zero mutation paths touched)

- **G-2** `admin/god-mode/page.js`: "Live Consoles" block restored at the foot of
  the sidebar — Trading Floor / Shockwave (destructive tooltip) / War-Map links,
  same markup + tooltips as the facilitator side. No flag checks: god_mode
  always passes the server console gates.
- **G-4** `admin/god-mode/page.js`: dead `case 'glossary_editor'` + its unused
  direct import removed. Glossary editing remains reachable — ResourceManager
  renders GlossaryManager in its own "📖 Glossary" tab (verified).
- **F-5** `components/DashboardHome.js` + call site + `config/sidebarConfig.js`:
  new `canAccessTab`/`role` props (default-permissive, so any other caller is
  unaffected). Every quick action and alert-card navigation is now gated by the
  same predicate the router enforces — no home-screen button can land on the 🔒
  panel. project_admin variant: alert section + briefing card suppressed,
  "👥 Facilitator Registry" quick action added (project_admin only).
  `ROLE_HIERARCHY.project_admin = 1` added, mirroring `admin_shared.py`.
- **F-8** `admin/facilitator/page.js`: Ctrl+1…N derived from the rendered
  `FILTERED_SIDEBAR` group ids (ref updated each render); shortcut sheet and
  bottom-bar hint show the role's true group count. Keys with no group no
  longer `preventDefault`.
- **F-9** consoles: ON/OFF switch labeled "PROJECT ON THIS SCREEN" with a
  scope-truth tooltip (war-map, trading-floor); error states split
  `auth` (401/403 → "sign in … then reload") vs `net` (backend unreachable)
  on all three consoles; war-map header shows "ROUNDS lo–hi IN PLAY" when
  cohorts diverge instead of the global max.
- **G-5** `admin/god-mode/page.js` MasterPasswordModal: copy now states
  (verified against `admin_router.py` — rotation only swaps the stored hash;
  no JWT/session revocation) that existing sessions stay signed in; local
  caps-lock hint added inside this modal only (shared `PasswordInput`
  deliberately untouched — it renders on player-facing surfaces).

**Explicitly NOT in S1** (per plan): shockwave auto-select removal and any
confirm changes (S3), ring-bell failure surfacing (S2), rehearsal button (S4).

## S1 gate evidence (run in-sandbox, 2026-07-11)

1. **Path whitelist** ✅ `git diff --name-only`: exactly 7 files, all
   `frontend/app/{admin,components,config}` — no backend/, no player page.js,
   no useSimulation, no shared player component.
2. **JSX parse** ✅ esbuild 0.28.1, all 7 files parse clean.
3. **Endpoint contract** ✅ regenerated and diffed against S0: **byte-identical**
   (the F-9 error handling changed `.then/.catch` continuation lines, not the
   fetch call sites; no endpoint, method, payload, or cadence changed anywhere).
4. **Backend pytest** ✅ 976 passed (baseline count).
5. **Player smoke** ✅ identical to S0 end-to-end, including R1 commit 201,
   all engines OK, and the expected R2-commit 429.

## S1 two-browser checklist (run on your machine)

- Role matrix — sign in as facilitator / lead / super_admin / project_admin:
  Dashboard-Home quick actions only show reachable tabs; project_admin home has
  Create Cohort + Facilitator Registry, no alert cards, no briefing card, and
  no button reaches the 🔒 "not available" panel.
- God Mode sidebar shows the three Live Console links; Shockwave keeps the
  DESTRUCTIVE tooltip; links open in a new tab.
- `?` sheet: Ctrl+1…5 shown for super_admin (5 groups incl. Administration),
  Ctrl+1…4 for facilitator/lead; each key toggles the matching group.
- Consoles: with an expired cookie → 🔒 "Signed out…" message; with the backend
  stopped → 🔌 "Backend unreachable — retrying…"; war-map with cohorts at
  different rounds shows "ROUNDS lo–hi IN PLAY".
- Master-password modal: caps-lock banner appears with Caps Lock on; copy shows
  the sessions-stay-signed-in sentence.
- Player screen side-by-side through one round: no unprompted change.

## Rollback

`git revert` the S1 commit — all items are rendering/navigation; no persisted
state, storage keys, or endpoint changes. Reverting cannot strand anything.

---

## Phase S2 — what changed (additive UI around existing calls; zero payload changes)

- **F-3(b)** `admin/trading-floor/page.js`: `ringBell` now acts on the POST
  result. Success → the exact pre-S2 sequence (bell sound, freeze, staggered
  reveal, confetti). Failure → the board **stays live**, a named red banner
  explains ("Bell NOT broadcast — players did not see the market close"), the
  button becomes "Retry the Closing Bell", and a busy state prevents
  double-fires. The request is byte-identical (same URL/method/no body); the
  403-profile case gets its own message. The bell sound no longer plays on a
  failed broadcast.
- **F-3(c)** same file: closed state gains "↺ Reopen board (this screen only)"
  — local state only, resumes the 5s poll, resets the reveal so a later
  re-close animates cleanly. Tooltip states the honest scope: players already
  received `market_close`; reopening does not retract it.
- **F-4** `components/FacilitatorManager.js` (shared-register component —
  dual-surface): dropping an .xlsx now **stages** it behind a pre-flight
  confirm ("accounts are created immediately on upload — no preview for
  .xlsx"; Cancel sends nothing). The response renders as a created ✓ /
  skipped ✗ checklist **including the one-time passwords the old toast
  discarded** (they were already in the response; the UI threw them away),
  with a copy-now warning. The drawer no longer auto-closes past the result.
  CSV/TXT path byte-identical. `closeDrawer` clears the new state.
- **G-1** `admin/god-mode/page.js`: header keeps one labeled "🔑 Password"
  button; the 🗝️ master-key entry moved to a red dashed "Break-Glass →
  Master Key…" item at the foot of the sidebar (below Live Consoles), opening
  the same modal. Routine and break-glass credentials are no longer twin
  icons 24px apart.

**Explicitly NOT in S2** (per plan): the ring-bell confirm + explicit cohort
target (S3/F-3a), shockwave auto-select removal (S3/F-1), rehearsal (S4).

## S2 gate evidence (run in-sandbox, 2026-07-11)

1. **Path whitelist** ✅ 3 files: trading-floor page, FacilitatorManager,
   god-mode page. No backend, no player files.
2. **JSX parse** ✅ esbuild clean on all 3.
3. **Endpoint contract** ✅ byte-identical to S0 (diff exit 0) — no call site
   added/changed; only handling around existing responses.
4. **Backend pytest** ✅ 976 passed.
5. **Player smoke** ✅ identical to S0 (R1 commit 201, engines OK, R2 429).

## S2 two-browser checklist (run on your machine)

- Backend stopped → Ring the Bell → red "Bell NOT broadcast" banner, board
  still polling once backend returns, button reads Retry, **no bell sound**;
  player screens show nothing. Backend up → Retry → behavior identical to S0
  capture (sound, freeze, reveal, confetti; player overlay appears).
- After a successful close → "Reopen board (this screen only)" resumes the
  live board; ring again → reveal animates from scratch.
- Registry (BOTH surfaces — God Mode tab and facilitator portal): drop an
  .xlsx → staged panel, Cancel → dev-tools shows no request; confirm → one
  POST identical to before; result panel lists created accounts WITH one-time
  passwords and skipped rows; drawer stays open until Done. Drop a CSV →
  flow pixel-identical to S0.
- God Mode header shows "🔑 Password" only; sidebar foot shows red dashed
  "Master Key…" that opens the master modal.

## Rollback

`git revert` the S2 commit. All additive UI; the only behavioral deltas are
facilitator-side (board stays live on failed broadcast; Excel waits for a
confirm) and revert restores the old behavior exactly.

---

## Phase S3 — destructive-console targeting (three independent commits)

**Invariant held everywhere: confirm-then-execute sends a request byte-identical
to S0; Cancel sends nothing. Only the gate in FRONT of each request changed.**

- **S3-A / F-1** `admin/shockwave/page.js` + new `components/shockwaveCatalog.js`
  + `__tests__/shockwave-catalog.test.js`:
  - Auto-select REMOVED — the console never chooses a target for you. The
    dashboard's `fac_selected_session` is offered as a visible, labeled
    prefill ("Prefilled from your dashboard cohort selection — change it
    above…"), never a silent default; anything else renders "— Choose a
    target cohort —" with Detonate disabled.
  - Cohort options show blast-radius context inline: name — N teams · R{n},
    computed from the leaderboard payload the page already fetched.
  - Detonation goes through the platform's tier-2 `useConfirm` impact preview:
    cohort NAME, team count, current round, per-team hit (derived from the
    catalog numbers, never hand-written), and an explicit 0-teams warning.
  - G-3 interim: the event catalog moved to one exported module whose numbers
    are verified against `backend/admin_router.py::_SHOCKWAVE_EVENTS` by a
    jest test that parses the backend source — an engine rebalance that
    forgets the console now fails CI instead of letting the console lie.
- **S3-B / F-3a** `admin/trading-floor/page.js`: Ring the Bell is now behind a
  tier-2 confirm whose impact line states the verified truth — the overlay
  reaches every connected player in ALL cohorts, not just the teams on the
  board, and reopening does not retract it. Cohort-id derivation and the POST
  are untouched.
- **S3-C / F-6** `components/CreateCohortModal.js` + `FacilitatorManager.js`
  (both dual-surface — test on God Mode AND facilitator portal):
  - One role resolution: the registry entry point passes the operator's real
    role (`operatorRole || 'super_admin'` fallback preserves legacy god-mode
    behavior) instead of hardcoding "super_admin".
  - Explicit project_admin branch, verified against `admin_router.py` gates:
    facilitator-assignment dropdown YES (provisioning; endpoints are
    require_facilitator), full config accordions YES (no longer the
    base-facilitator lockdown), System Engine Modules NO (its PATCH is
    require_super_admin server-side — the UI must not promise above the server).
  - The assignment never defaults to the `project_admin` virtual account.

## S3 gate evidence (run in-sandbox, 2026-07-11)

1. **Path whitelist** ✅ 6 files across the 3 commits — all admin-side; no
   backend, no player files.
2. **JSX parse** ✅ esbuild clean on every edited/created file, per commit.
3. **Endpoint contract** ✅ byte-identical to S0 (diff exit 0). No fetch site
   added, removed, or altered — including the shockwave POST body and the
   ring-bell POST.
4. **Frontend jest** ✅ 63 passed / 5 suites, including the new
   shockwave-catalog drift tripwire (which parses the backend source).
5. **Backend pytest** ✅ 976 passed.
6. **Server-behavior re-proof** ✅ re-ran the S0 capture script end-to-end:
   shockwave 200, teams_hit 1, KPI delta exactly −$6,000,000 / −6; bell 200
   `bell_rung`; rehearsal still a KPI no-op. The backend contract the new
   confirms sit in front of is unchanged.
7. **Player smoke** ✅ identical to S0 (R1 commit 201, engines OK, R2 429).

## S3 two-browser checklist (run on your machine — the critical phase)

- Shockwave console, nothing selected on the dashboard: no cohort pre-picked,
  Detonate disabled with tooltip. Select cohort A on the facilitator
  dashboard → open console → amber "prefilled from your dashboard selection"
  note; change the dropdown → note disappears.
- Detonate on a THROWAWAY cohort: confirm shows the right name/team count/
  round and the per-team hit; **Cancel → dev-tools shows zero requests**;
  confirm → one POST, body identical to S0 (`event_id`, `countdown`), player
  takeover appears, KPIs move by exactly the previewed amounts.
- Ring the Bell: confirm states the ALL-cohorts scope; Cancel → no request;
  confirm → S0-identical behavior (sound, freeze, reveal, player overlay in
  every cohort — verify with two players in two different cohorts).
- CreateCohortModal role matrix at BOTH entry points (Dashboard Home button /
  Registry row action): project_admin sees the same modal both ways —
  facilitator dropdown present, engine/verticals/modules/interventions
  accordions present, System Engine Modules section ABSENT; super_admin and
  base facilitator unchanged vs S0 screenshots; a cohort created by
  project_admin lands on the chosen facilitator, not on "project_admin".
- Run a live round on a second cohort while detonating on the throwaway one:
  the live cohort's players see nothing; round timing unchanged.

## Rollback

Each item is its own commit — revert selectively (`189097c` shockwave,
`d12ffb2` bell, `8c9f799` modal). Payloads unchanged ⇒ reverting a gate
cannot leave the backend inconsistent; worst case is the old blind confirm
reappearing.

---

## Phase S4 — rehearsal mode surfaced (F-2; the ONE new request variant in v3)

`admin/shockwave/page.js` only:

- **"🎭 Rehearse (no student impact)"** sits LEFT of Detonate (rehearse-first
  by design). Same endpoint, same body plus the server's documented WOW-4E
  flag `rehearsal: true`. No confirm on rehearsal — it is the safe path and
  friction there would push people toward the live button.
- The preview card renders from the POST response (no WS handling needed):
  REHEARSAL badge, title, narrative, per-team treasury/reputation numbers,
  countdown, and the attribution note (`shockwave_rehearsal` in the audit
  trail). 403-profile shows the same named error as detonation.
- Detonate/rehearse clear each other's result cards; busy state prevents
  double-fires.

**Declared contract delta (the phase's entire point):** the static
endpoint-contract diff is empty — the rehearsal fetch's call-site line is
textually identical to the detonate one; the real delta is the `rehearsal:true`
body field, which the static extraction cannot see. It is declared here and
proven below instead of smuggled.

## S4 gate evidence (run in-sandbox, 2026-07-11)

1. **Path whitelist** ✅ 1 file (`admin/shockwave/page.js`).
2. **JSX parse** ✅ clean.
3. **Endpoint contract** ✅ no new call site (delta = body field, declared above).
4. **Live no-op proof** ✅ (the phase's acceptance test, run end-to-end):
   - Rehearsal POST → 200, `status:"rehearsal"`, "students NOT affected".
   - Throwaway player's KPIs **byte-identical** before/after
     (treasury 6,500,000 / reputation 44.0 both sides).
   - Audit trail contains the `shockwave_rehearsal` entry (id, timestamp,
     cohort_id, event_id) — rehearsals are attributable.
   - Real detonation fired AFTER a rehearsal is unaffected: cyber_attack
     landed exactly −$4,000,000 / −7 (catalog values), `teams_hit: 1`.
5. **Frontend jest** ✅ 63/63 (catalog tripwire included).
6. **Backend pytest** ✅ 976 passed. **Player smoke** ✅ identical to S0
   (201 / engines OK / R2 429).

## S4 two-browser checklist (run on your machine)

- With a player connected to a throwaway cohort: Rehearse → preview card on
  YOUR screen; the player screen shows **nothing**, no re-render, no flicker
  (this is the single most important check in the phase).
- Rehearse then Detonate the same crisis → detonation behaves exactly as the
  S3 checklist (confirm → takeover → KPI delta equals the preview numbers).
- Profile with `shockwave_enabled` off → Rehearse shows the same "disabled
  for your facilitator profile" error as Detonate.
- God Mode → Activity & Complexity / audit: the rehearsal appears as
  `shockwave_rehearsal` with the cohort and event id.

## Rollback

`git revert` the S4 commit removes the button and preview; rehearsal writes no
state, so no residue is possible by construction (and by the proof above).

---

## Phase S5 — the sign-off-gated backend items (additive only, feature-detected)

- **S5-1 / F-7** — turned out FRONTEND-ONLY: the login and `/auth/refresh`
  responses have always carried the `permissions` boolean map; the login
  handler's destructure dropped it. Fix: cache it (C-2 safe — booleans, no
  PII) and gate "Create New Cohort" on `permissions.can_create_cohorts`,
  falling back to the old role heuristic when the flag is absent (older
  cached auth, project_admin virtual account). **Visible behavior change
  that is the point of the fix:** a lead whose flag was toggled off (e.g.
  FAC-001 in the current registry has `can_create_cohorts: false`) now loses
  the button instead of hitting a server rejection after filling the form.
- **S5-2 / G-3 proper** — `GET /api/admin/shockwave/events` serves
  `_SHOCKWAVE_EVENTS` (require_facilitator). The console prefers the engine's
  catalog and keeps frontend emoji labels by id; on ANY failure it falls back
  to the local `shockwaveCatalog`, which remains guarded by the S3 drift-
  tripwire jest test. +2 pytest (route exists & gated — a 404 would mean the
  path got shadowed by a dynamic /{cohort_id} route; payload matches engine).
- **S5-3 / F-4 proper** — parse-only
  `POST /api/admin/facilitators/bulk-upload/preview` (require_registry_admin).
  Deliberately a DISTINCT route, not a `dry_run` flag: FastAPI ignores unknown
  params, so a flag on the create endpoint would make an old backend silently
  CREATE accounts on a "preview" request. Parsing was extracted verbatim into
  `_parse_bulk_upload_sheet`, shared by preview and create so the two can
  never disagree. The Excel staged panel now shows a real preview table
  (row numbers, names, per-row skips, "Create N accounts now"); a 404/405
  falls back to S2's blind-confirm flow. +3 pytest (gated route; preview
  parses and creates NOTHING — registry length asserted; preview/create
  agree row-for-row on the same file, with post-test registry cleanup+persist).

## S5 gate evidence (run in-sandbox, 2026-07-11)

1. **Backend pytest** ✅ **981 passed** = 976 baseline + 5 new (2 catalog,
   3 preview). No existing test changed.
2. **Live endpoint checks** ✅ catalog GET 200 with all 4 event ids (route
   not shadowed); login response carries `permissions`
   (`can_create_cohorts: false` for FAC-001 — the F-7 case, live); preview
   returns 403 for a lead facilitator (registry-admin gate holds).
3. **Frontend jest** ✅ 63/63 (tripwire still green against the edited
   backend source).
4. **Endpoint contract** ✅ exactly the two declared additions (catalog GET,
   preview POST); committed snapshot updated with the declaration header.
5. **Old-frontend compatibility** ✅ by construction: one response field
   already existed, two endpoints are new paths no old frontend calls.
   **New-frontend-vs-old-backend** ✅ by feature-detect: missing catalog →
   local copy; preview 404/405 → blind-confirm flow; missing permissions →
   role fallback.
6. **Player smoke** ✅ identical to S0 (201 / engines OK / R2 429).
   **Repo hygiene** ✅ the user's `db/facilitator_registry.json` untouched
   (all live tests ran against the /tmp sandbox copy; the pytest cleanup
   persists the cleaned registry).

## S5 on-machine checklist

- Sign in as a lead with `can_create_cohorts` OFF → no Create button on
  Dashboard Home (after one fresh login to refresh the cached auth); toggle
  it ON in the Registry → button returns on next login/refresh.
- Shockwave console with the new backend → crisis cards show engine numbers
  (change one in `_SHOCKWAVE_EVENTS` on a dev copy: card updates, jest
  tripwire fails until the local catalog is synced — both layers work).
- Registry (both surfaces): drop an .xlsx → real preview table appears,
  "Create N accounts now"; drop a sheet with a nameless row → that row is
  listed as skipped BEFORE anything is created; against an older backend
  (or with the preview route blocked) → the S2 blind-confirm copy appears
  instead.
- `must_change_password`/one-time-password flows for bulk-created accounts
  unchanged.

## Rollback

Three independent commits — revert selectively. Backend reverts are safe:
both endpoints are additive reads/parse-only (no state writes), and the
create endpoint's refactor is covered by the preview/create-agreement test.
Frontend degrades gracefully in every mixed-version direction by design.

---

## Phase V-A (player dashboard v2) — retrospect to the recap + owner-requested removal

First player-facing phase; scope from
`REVIEW_Muressons_PlayerDashboard_v2_Simplification.md` (V-3) plus one direct
owner request. Files: `EngineEventsPanel.js`, `ExecutiveCockpit.js`.

- **V-3 move:** `EngineEventsPanel` gained a `sections` prop
  ('all' = pre-V-A behaviour for any untouched caller · 'retrospect' =
  What Happened This Round + Road Not Taken · 'rest' = CEO Diary). The
  RESULTS stage of the Decision Canvas now renders the retrospect (after the
  Key Events summary, against the just-committed state) — the counterfactual
  lands where the learning does. The rail renders `sections="rest"` plus a
  one-line "Round recap ▸" link that reveals the retrospect on demand
  (collapsed by default; shown from R2 / post-commit). Same component, same
  data, zero fetch changes.
- **V-A+ (owner request, screenshot 2026-07-11):** the "Active Infrastructure
  Projects" panel (working-capital DSO / synergy timers with "1 Turn Left")
  removed from the player screen entirely, including its dead `infraOpen`
  state and `pendingProjects` derivation. Display-only:
  `pending_capex_projects` remains in the /dashboard payload untouched.
  Restore = revert this commit.

### Gates (in-sandbox, 2026-07-11)
1. JSX parse ✅ both files. 2. Endpoint contract ✅ unchanged vs the S5
snapshot (no fetch/WS call site touched). 3. Frontend jest ✅ 63/63.
4. Player smoke ✅ identical (R1 commit 201, engines OK, R2 429).

### Two-browser checklist (your machine)
- Play R1 → commit → results stage shows result cards → ConsequenceReplay →
  Key Events → **What Happened + Road Not Taken** (open by default) →
  waterfall. Advance to R2: the rail shows the collapsed "Round recap" link;
  opening it reveals both accordions with R1 data; CEO Diary unchanged in
  the rail.
- The Active Infrastructure Projects panel no longer appears anywhere
  (previously center column, after CAROIC/history, when projects pending).
- Focus-mode auto-advance, commit payloads, and round transitions unchanged
  (stage machine untouched).

### Rollback
One commit — `git revert` restores both the ambient rail accordions and the
infrastructure panel.

---

## Phase V-B (player dashboard v2) — locked-state truth + single homes

File: `ExecutiveCockpit.js` only. Scope: V-2 + V-4 from the v2 review.

- **V-2 locked options:** pre-gate (`!canAccessStrategy` — briefing unread,
  R1 map / R2 CSRD incomplete, or R5 audit pending), the deep-dive Strategic
  Options section renders 🔒 locked summary chips (letter + title + cost)
  with a hint naming the exact unlock, instead of full option prose behind a
  click-intercept. The Strategic Breakdown comparison matrix is withheld with
  it (it is option prose too). The glance-mode minis gain a 🔒 prefix.
  Post-gate render is byte-identical to before; the canvas strategy stage is
  untouched; the click-intercept + warning toasts remain.
- **V-4 single homes:**
  - The round directive is no longer client-injected as Market-Reality-Feed
    item 1 (`crisisInfo` push removed) — it lives in the round-narrative card
    and the header chip. Server-sent mailbox items untouched (data flow).
  - The rail's "Re-enter Focus Mode" button removed — the left FOCUS MODE
    pill and the stepper remain (three affordances → two, one per surface).
  - **Descoped consciously:** the plan's "fold FTSE benchmarks into the
    Analytics drawer" — on code inspection the FTSE panel (sector ESG
    benchmarks) and the rail's Nordhaven bar (rival EV race) carry DIFFERENT
    data, and the FTSE accordion already collapses by default. Not a
    duplication; moving it would be churn without a finding.

### Gates (in-sandbox, 2026-07-11)
JSX parse ✅ · endpoint contract unchanged ✅ (the removed feed item was a
client-side array push, not a fetch) · jest 63/63 ✅ · player smoke identical
(201 / engines OK / R2 429) ✅.

### Two-browser checklist (your machine)
- R2 pre-CSRD: options section shows three 🔒 chips + "Complete the CSRD
  Assessment to unlock"; no comparison matrix; clicking still explains why.
  Complete the CSRD → full tiles + matrix return exactly as before; select +
  commit flow unchanged.
- Market Reality Feed no longer opens with the directive item; the narrative
  card and header chip still carry it; mailbox unchanged.
- Right rail has no "Re-enter Focus Mode" button; the left FOCUS MODE pill
  re-enters the canvas as before.
- R1 (map gate) and R5 (audit gate) show the same locked treatment with the
  right unlock hint.

### Rollback
One commit — revert restores the prose-behind-intercept render, the feed
injection, and the rail button.

---

## Phase V-C (player dashboard v2) — one primary per column + docked stepper

Files: `ExecutiveCockpit.js`, `RoundChecklist.js`. Scope: V-1 + V-6.

- **Exclusive center column (V-1), stage-aware:** the deep-dive stack
  (options + matrix simultaneously, each behind its own click-intercept) is
  now sequential like the flow itself:
  - Pre-decision: full options section (V-B's locked chips pre-gate);
    the allocation matrix is a 🔒 one-liner naming its unlock ("unlocks
    after your strategic decision") that still explains on click. The old
    invisible click-intercept over a fully-rendered matrix is gone.
  - Post-decision: options fold to a ✓ one-line summary (choice, title,
    cost) with a "Change" button; the matrix renders full and becomes the
    single primary work surface. Choosing again re-folds automatically;
    round change resets. Pillar mode (multi-select worksheet) is exempt
    from the fold by design. `tour-strategic-target` / `tour-capital-target`
    ids preserved in every branch (onboarding tour keeps its anchors).
  - Selection/allocation handlers, gating flags, and commit flow untouched.
- **Single-open rail (V-1):** while a rail tab panel (Mailbox / Decisions /
  Engines / Climate) is expanded, the Market Reality Feed folds to a
  one-line header (click restores it by collapsing the panel). **Active
  alerts override the fold** — escalation keeps its rights; an alert always
  renders the full feed surface.
- **Docked stepper (V-6):** `RoundChecklist` no longer `position:fixed`es
  itself out of its mount (which is why it floated over the Option A card)
  and is no longer dismissible — the ✕ and the collapsed-pill state are
  gone, replaced by a compact N/M counter. Its mount moved from the top of
  the center console to a sticky footer at the bottom of the scroll area:
  always visible, never overlapping (the old 80px anti-overlap spacer is
  retired with the float).

### Gates (in-sandbox, 2026-07-11)
JSX parse ✅ both files · endpoint contract unchanged ✅ · jest 63/63 ✅ ·
player smoke identical (201 / engines OK / R2 429) ✅.

### Two-browser checklist (your machine — walk all five stages)
- R1 pre-decision, deep dive: options full, matrix = 🔒 one-liner (click
  explains). Choose Option B → options fold to "✓ B — … · Change", matrix
  expands; Change → full options return; choose C → re-folds. Allocate and
  commit — payload identical to before.
- Onboarding tour (fresh session): the strategic and capital tour steps
  still anchor correctly in both pre- and post-decision states.
- Rail: open Mailbox → feed folds to its one-liner; collapse → feed returns.
  Trigger a crisis alert (god-mode) with Mailbox open → the full feed/alert
  surface renders despite the open tab.
- Stepper: bottom of the center column, sticky while scrolling, nothing
  renders under it illegibly, no ✕; on 1366×768 it doesn't wrap over content.
- Esc / 1–4 BU switching unchanged; glance mode unchanged.

### Rollback
One commit — revert restores the stacked center, the always-on feed, and the
floating dismissible checklist.

---

## Phase V-D (player dashboard v2) — token adoption + concentration + governance

Scope: V-5 + V-7 + the slotting rule. Files: `MarketIntelCards.js`,
`MarketTicker.js`, `EngineEventsPanel.js`, `ConsequenceReplay.module.css`,
`LivingPlanet.module.css`, `DecisionPressureTimer.module.css`,
`ExecutiveCockpit.js` (one effect), `CLAUDE.md`.

- **V-5 token pass (zero visual change by construction):** 73 exact-value
  hex→token replacements across the six post-redesign surfaces
  (`#ef4444→var(--danger)`, `#4ade80→var(--positive-text)`,
  `#f59e0b→var(--caution)`, `#6366f1→var(--accent)`, brand/info families,
  etc.). Values are identical today; the point is that the accreted surfaces
  now repaint with the token file instead of being stranded on literals.
  **Deliberately descoped:** `AnnualReport.js` (39 hexes across canvas+SVG —
  var() is unsafe in canvas fillStyle and SVG presentation attributes) and
  the SVG-bearing JS of LivingPlanet/PressureTimer; and NO hue retirements
  (e.g. Road-Not-Taken purple → accent) — per the tokens.css Phase-B note,
  hue decisions happen on a real screen, not in a blind regex. Both descopes
  are one-line changes later because of this pass.
- **V-7 concentration:** the `data-allocation-open` dim flag (consumed by
  MarketTicker via MutationObserver) now also sets during BU drill-down
  (`isDeepDive`) — the ticker dims while inspecting, same as during
  allocation/commit.
- **Governance:** the slotting rule (one slot per surface, tokens mandatory,
  retrospect-to-results, locked-summary pattern) is now in `CLAUDE.md`
  alongside the tooltip-truth and catalog-tripwire conventions — the
  accretion-prevention rule the v2 review §5 called the actual fix.

### Gates (in-sandbox, 2026-07-11)
JSX parse ✅ all touched JS · CSS files rename-refreshed ✅ · endpoint
contract unchanged ✅ · jest 63/63 ✅ · player smoke identical
(201 / engines OK / R2 429) ✅. Guard-grep confirmed no `fill="var(`/
`stroke="var(` was introduced (no SVG-attribute damage).

### Two-browser checklist (your machine)
- Visual spot-diff of the six surfaces vs pre-V-D screenshots — they should
  be pixel-identical (indirection only). If anything shifted hue, a literal
  was not at its token's exact value: flag it.
- Enter a BU drill-down → the bottom ticker dims; exit → restores. Focus
  allocation/commit dimming unchanged.
- `prefers-reduced-motion` still collapses animations (tokens.css Phase E).

### Rollback
One commit — revert restores literals, the narrower dim condition, and
removes the CLAUDE.md sections.
