# Muressons — Product & UX Audit
**Player end + Facilitator end · 2 August 2026**
Reviewed against commit state in `muressons-sim` (backend ~106k LOC Python, frontend ~80k LOC JS/Next.js App Router, CSS Modules).

Labels used throughout: **[F]** fact observed in the repo · **[I]** inference from code patterns · **[A]** assumption I could not verify from code.

---

## 1. What I found

**Architecture [F].** FastAPI backend + Next.js (JavaScript, not TypeScript) frontend, CSS Modules. Storage is dual-backed and chosen at boot (`backend/main.py:171-186`): Postgres if reachable, otherwise an in-memory dict store that snapshots to a single JSON file (`backend/database_memory.py:93-157`). The simulation model itself is a clean, pure-function core — `engine.py`, `round_logic.py`, `terminal_valuation.py`, `systemic_risk_engine.py` — explicitly documented as no-I/O and pinned by a golden-trace regression test (`backend/tests/test_stakeholder_golden_trace.py`). That separation is real and it is the reason a UI-layer pass is feasible at all.

**Player journey [F].** Player ID + password → `POST /public/sessions/{id}/join` (`backend/router.py:648`) → username prompt → round briefing → 7-step spotlight tour → cockpit. Inside a round the stage machine is `useRoundStage.js:30`: `gate?` (R1 stakeholder map / R2 materiality matrix) → `strategy` → `allocation` → commit → `results`. Decisions live in page-level React state, autosaved every 30 s (`page.js:830-837`), freely revisable until commit. Commit opens one "Predict Before You Commit" review modal, then an 800 ms ceremony, then the POST. After committing, a multi-team cohort shows a "Waiting for Other Teams — X/Y committed" barrier (`ExecutiveCockpit.js:2210-2227`, `4320-4356`).

**Facilitator journey [F].** Sign in → create cohort (one modal, 7 accordion sections, 84 `useState` hooks, up to 11 sequential HTTP calls with a partial-failure retry panel, `CreateCohortModal.js:682-839, 996-1092`) → mint players individually or by Excel bulk upload (ceiling 20, `player_capacity.MAX_PLAYERS_CEILING`) → run from a 33-tab sidebar (`config/sidebarConfig.js`) plus 3 external full-screen consoles → debrief via chart dashboards → CSV/JSON export.

**State machine [F].** There is no single round-state enum. Round state is a composite of: (a) each team's own round number — a team *is* an independent child session with its own round chain, `parent_cohort_id` linking it to the cohort; (b) cohort pacing policy in a **separate, process-local** store `_round_pacing` (`admin_shared.py:1373`) with modes `free | manual | timed` and an `unlocked_round` integer; (c) transient flags (`_fa_force`, global `system_frozen`).

Transitions: commit (`router.py:1795` → `_commit_turn_impl` → `engine.process_tick` → `db.insert_next_round`) is the only forward transition, and **commit == resolve** — there is no submit-then-resolve seam. Unlock (`admin_router.py:3567`) increments `unlocked_round` with no cap and no inverse. Force-advance (`admin_router.py:3373`) sets a flag that is consumed lazily on some *other* team's next dashboard poll, which auto-commits laggards from saved drafts, or from a hardcoded fallback of `option_b` + `$1` capex per BU (`router.py:248-273`). Undo (`admin_router.py:8474`) **deletes** rows — including the audit rows — behind the immutability triggers, and is itself not audited. Concurrency is well defended: per-session asyncio lock, Postgres advisory lock, `expected_round` optimistic check, 5 s cooldown, and a `UNIQUE(session_id, round_number)` backstop, with dedicated race tests.

**Sync [F].** No push for the common case. ~15 independent `setInterval` polling loops across the app (5 s auto-advance detect, 30 s autosave, 15 s cohort pulse, 5 s pacing, 10 s registries…). WebSockets exist but carry only "go re-fetch" nudges, and a normal commit pushes nothing to siblings or the facilitator.

**Uncertain [A].** Whether production runs Postgres or memory mode; actual cohort sizes and whether teams share one login in practice; whether facilitators use Manual pacing today (see 5.1 — if they do, they have been fighting a broken button).

---

## 2. What's working and must be protected

Short, as requested.

1. **The simulation core is properly quarantined.** Pure-function engines, a golden-trace oracle, integrity bounds tests, and mutation guards asserting `process_tick` never mutates inputs. Every recommendation below sits outside this boundary.
2. **Commit concurrency is genuinely well engineered** (`router.py:1811-1941`). Do not "simplify" it.
3. **`ConsequencePreview` + `DecisionTile` trade-off hints** (`DecisionTile.js:42-51`). Showing the projected cost/benefit of an option *before* selection is the single most pedagogically valuable thing in the player UI. Most simulations don't do this.
4. **`SustainabilityBalancedScorecard.js:256-267` and `MirrorDebrief.js`.** Endgame M_R attribution written in plain causal English ("Earned +0.30 by achieving Synergy ≥ 80 through circular integration in R7") and counterfactual "biggest missed lever" analysis. This is world-class debrief content — it is just delivered too late and to the wrong person (see 5.12).
5. **`ConfirmModal.js`** — the one dialog in the codebase with `role="dialog"`, `aria-modal`, Escape-to-close and autofocus. It should become the template, not the exception.
6. **`ErrorBoundary.js`** wrapping the whole app in `layout.js:75-79`.

---

## 3. Audit — Player end

### First five minutes — **Weak**
- The onboarding chain is username prompt → briefing → 7-step tour (`OnboardingWalkthrough.js:13-57`), all fully skippable with no read-confirmation. **[F]**
- There is **no explicit statement of the objective anywhere in the first five minutes**. The tour's welcome step says only "Your decisions over 10 rounds will shape the company's future" (`OnboardingWalkthrough.js:16`). The actual scored objective — Year-5 Terminal Valuation and the Regenerative Multiple — surfaces contextually in Round 10 content and in the endgame scorecard. A participant cannot answer "what am I optimising for" from the screen. **[F]**
- Academic framing (the Theory Card) is **off by default** (`RoundBriefing.js:236`). So the pedagogical scaffolding that would teach the causal model ships disabled.
- Onboarding completion is not persisted: `showOnboarding` is plain `useState` (`page.js:452-453`) and `seenBriefingRoundsRef` is deliberately reset on every `sessionId` change (`page.js:430-435`). A player who refreshes during Round 1 replays the briefing and the full 7-step tour. **[F]**

### Mental model & scenario comprehension — **Adequate**
- The UI does more than collect inputs: `ConsequencePreview.js:80-232` renders impact bars, stakeholder reactions and tipping-point proximity for the currently selected option. **[F]**
- But its M_R Terminal Valuation section is dead — the call site hardcodes `whatIfResult={null}` (`ExecutiveCockpit.js:4168`), so a permanently-empty panel renders with no explanation. **[F]**
- The causal model is taught *reactively* (after you pick) rather than *structurally* (here is the machine you are operating). There is no persistent model diagram on the player side, though a rich one exists for facilitators (`admin/war-map`).

### Decision-making surface — **Strong**
- Three options rendered side by side with per-option projected trade-offs computed pre-selection (`ExecutiveCockpit.js:2732-2760`, `DecisionTile.js:42-51`). **[F]**
- Full revisability until commit, plus a "Change" affordance to reopen the tiles (`ExecutiveCockpit.js:2573-2580`). **[F]**
- 30 s autosave with stale-round protection (`page.js:693-701`). **[F]**
- Weak spot: over-allocation is surfaced only as a warning banner (`ExecutiveCockpit.js:1962-1966`) and a red button state; the CSF cap is enforced server-side, so the player can walk to the confirm screen in an invalid state.

### Feedback & results legibility — **Adequate**
- `ConsequenceReplay.js:28-98` builds a decision → mechanism → impact → consequence chain and auto-plays it. Real causal explanation. **[F]**
- But it is assembled from a **hardcoded list of event keys** (`talent_penalty_applied`, `loan_interest_payment`, `cyclone_loss`, plus the first 3 truthy flags). Any engine effect not on that list is silently absent, so the "why" is systematically incomplete and the gaps are invisible. **[F]**
- Round results attribute to *mechanism* ("Brain-Drain inflated Software OPEX by X%"), never to *your choice* ("you picked Option B in R3, which is why…"). Choice-level attribution only exists at endgame. **[F]** This is the classic place simulations fail as learning tools, and Muressons is halfway across.

### Time and pressure — **Weak**
- `DecisionPressureTimer.js` returns `null` entirely when `pacing.mode === 'free'` (`:84`) — the default mode. So in the default configuration **there is no deadline surface at all**. **[F]**
- When it does render, it lives in the fixed 48 px cockpit header (`ExecutiveCockpit.module.css:138-151`) which does not scroll away — good. But it is fully occluded during the round briefing, the crisis screen, the onboarding tour, the Predict-Before-Commit modal, and the stakeholder-map / materiality slide-ins (`page.js:1352-1393, 1785-1928`), all of which replace or cover the cockpit tree. A deadline can run out entirely inside a sub-flow. **[F]**
- At zero, the server auto-commits and the client shows a toast that **auto-dismisses after 5 seconds** (`page.js:1728-1745`), with no record anywhere of what was submitted on the player's behalf. **[F]**

### Team collaboration — **Critical gap**
- `backend/router.py:649-651`: *"Registers a player into a cohort by creating an independent session for them. Each player gets their own game state."* One player ID = one session = one company. **[F]**
- `team_consensus: 'majority'` is sent on every commit as a **hardcoded string literal** (`page.js:788`) with no UI that collects it. **[F]**
- Nothing prevents two browsers on the same player ID from editing and committing concurrently; the double-submit guard `commitInProgressRef` is an in-memory ref scoped to one tab (`useSimulation.js:49,401-405`). Cross-tab races fall through to the server 409, which surfaces as a generic error toast. **[F]**
- **The honest reading — confirmed by you (§11 Q2): one login per person, so there are no teams at all.** Every participant runs their own company, and the "team" vocabulary layered on top ("Waiting for Other Teams", `team_consensus`, "X/Y teams committed") describes a collaboration model that does not exist. The cost is not just confusing copy: a fabricated consensus value sits in a graded audit log, and if your pedagogy *wants* team deliberation, nothing in the product hosts or records it. See recommendation 7.7.

### Irreversibility & error prevention — **Weak**
- **The gates run after the confirmation.** `attemptCommitTurn` (`page.js:1281-1313`) is wired as the prediction modal's `onCommit` (`page.js:1647`). So the sequence is: click Commit → review your decisions → click "✓ Confirm & Commit" → *then* get told "This round's quiz is mandatory" / "You must complete the Stakeholder Grid". Confirmation before validation. **[F]**
- The confirm modal's three actions — "← Go Back & Edit", "Skip & Commit", "✓ Confirm & Commit" — put the escape hatch and an immediate irreversible commit **adjacent and in the same visual class** (`.predictionSkip` for both, `ExecutiveCockpit.js:3772-3783`). **[F]** This is a misclick machine.
- No undo after commit on the player side, which is correct for the pedagogy — but it raises the bar on the confirm step, which is currently the weakest link.

### Waiting states — **Adequate**
- The cohort barrier does exist and is decent: "⏳ Waiting for Other Teams — 3/5 committed — auto-advances in ~120 s" (`ExecutiveCockpit.js:4337-4353`). **[F]**
- But it appears only *after* commit, inside the results overlay. During the decision phase there is no sense of the room at all. **[I]** In a live workshop that dead air is where engagement dies.
- The 800 ms commit ceremony fires **before** the network request and is torn down before the POST starts (`page.js:1307-1312`). There is no in-flight indicator: `sim.loading` exists in `useSimulation.js` and is **never read in `page.js`**. On a congested classroom LAN, a slow commit is a completely dead UI. **[F]**

### Continuity — **Adequate → Weak**
- Server-keyed identity means a player can re-login on any device and resume (`router.py:702-711`). Good. **[F]**
- `resumeSession` clears the cached session id on a failed dashboard fetch (`useSimulation.js:695-704`) while `page.js:335-339` carries a comment explicitly saying it must not — the two disagree and the wipe wins. A transient backend blip logs the player out. **[F]**
- Uncommitted work is protected only by the 30 s autosave, which fails silently to `console.error` with no retry (`page.js:825-827`). No `beforeunload` guard, no local draft. **[F]**
- **Staleness detection is effectively dead.** `connectionState` flips to `stale` after 2 consecutive `fetchDashboard` failures (`useSimulation.js:287-288`), but `fetchDashboard` is only called reactively from ~6 sites; the actual 5 s background poll uses its own raw `fetch` and swallows errors (`useSimulation.js:675`). A player can be offline for an entire decision phase and see no banner. **[F]**

### Accessibility — **Critical gap (fails WCAG 2.1 AA)**
- **2.1.1 Keyboard, on the core interaction.** In the legacy A/B/C paradigm the strategic option tiles are `<div … onClick>` with no `role`, no `tabIndex`, no key handler (`ExecutiveCockpit.js:1804-1808`). The primary decision of the entire product is mouse-only for any cohort not on `multi_toggles`/`brsr_ngrbc`. **[F]** (Pillar mode is fine — `PillarSelectDropdown.js` uses real buttons and listbox roles.)
- 38–96 clickable `<div>`s app-wide depending on counting method; a scan of their opening tags found **zero** with `tabIndex`, `role="button"` or a keyboard handler. **[F]**
- **1.4.3 Contrast.** Computed against the literal token values in `globals.css`: in light mode `--kpi-good` `#059669` gives 3.44–3.77:1 on the four surfaces and `--kpi-warn` `#d97706` gives 2.91–3.19:1 — both fail AA. The file's own comment claims these are "tuned for a bright room… keep 4.5:1+ contrast on white surfaces." **[F]** That comment is false by measurement, and "bright room" is exactly the classroom case.
- **4.1.2 / 2.4.3.** 6 of 8 modals (`CFOOverrideModal`, `JoinCohortModal`, `ChangePasswordModal`, `BalanceSheetModal`, `StakeholderMapModal`, `UsernamePromptModal`, `CreateCohortModal`) have no `role="dialog"`, no `aria-modal`, no Escape handling, no focus trap, no focus restore. `ConfirmModal.js` has everything except the trap and restore. **[F]**
- Touch targets: 14 px checkboxes (`JoinCohortModal.module.css` `.checkbox`), 22–28 px toggles and close buttons across 9 files — below the 24 px floor in several cases. **[F]**
- Credit where due: `prefers-reduced-motion` is respected globally in both `globals.css:999-1008` and `tokens.css:163-169`, plus 8 component-level overrides. **[F]**

### Motivation & narrative — **Strong**
- The cockpit framing, market ticker, crisis interrupts, archetype reveal and front-page reveal all land. This does feel like running something. **[F]** The risk is the opposite one: ceremony without substance (the 800 ms fake processing animation is literally that).

---

## 4. Audit — Facilitator end

### Pre-run setup — **Weak**
- One modal, 7 collapsible sections openable in any order, **84 `useState` hooks**, and a submit path that fires the cohort create plus **up to 10 further sequential PUT/PATCH/POST calls** (`CreateCohortModal.js:682-839`). If step 6 of 11 fails, the cohort exists in a partially-configured state and the facilitator repairs it through a "setup-integrity panel" (`:996-1092`). **[F]** That panel is a well-built band-aid over an architecture problem.
- Hard validation covers exactly two fields (`regionId`, `industryVertical` in single-BU mode, `:913-931`) out of dozens of settable options, several of which are permanent on create — the button literally says *"Permanently Lock & Create Cohort"* (`:3250`). **[F]**
- **[I]** For a first-time instructor this is the highest-anxiety screen in the product: maximum irreversibility, minimum guidance, no dry-run of the resulting configuration before locking.

### The control room — **Critical gap**
This is the headline finding.

- **Every player can see "3/5 teams committed." The facilitator cannot.** The tally is computed server-side by `_cohort_commit_progress` (`router.py:185-211`) and injected into every *player's* dashboard payload (`router.py:1733-1736`). No admin endpoint returns it. `DecisionPressureTimer.js` — the component that renders the badge — is mounted only in `ExecutiveCockpit.js:1227`, the player board. **[F]**
- The facilitator's nearest equivalent, `CohortPulse.js`, is a KPI heatmap on a 15 s poll (`:62`) that renders **no submission status at all** — despite its own registry tooltip promising "commit progress, and sentiment" (`config/analyticsRegistry.js:44`). **[F]**
- Its backend already returns `"round": latest_rn` per team (`admin_router.py:10820`). The data is on the wire and thrown away by the client. **[F]** This is the cheapest high-value fix in the audit.
- "Who is connected / who is stuck": nothing. `PlayerRegistry.js` renders only `created_at` (`:728`) though its sidebar tooltip promises "active/inactive connection status" (`sidebarConfig.js:122`). **[F]**
- "Is anything broken": `SessionHealthDashboard.js` exists and is wired **only into God Mode** (`admin/god-mode/page.js:618`). A plain facilitator cannot reach it. **[F]**
- Net: to answer "who is stuck", a facilitator opens teams one at a time through `session_viewer` / `impersonate`. In front of a room, at 15–20 people, that is not a workflow.

### Intervention tools — **Adequate**
- Real inventory: force-advance (`RoundPacingControl.js:183`), undo round incl. cohort-wide with typed confirmation (`UndoRound.js:44-77`), custom black swan injection, broadcast/bulk messaging, swipe files, shockwave console, auto-pause thresholds, three narrative overrides. **[F]**
- Two credibility problems:
  - **Manual override is 3 hardcoded events** (`carbon_tax`, `omni_tech_poach`, `force_strike` — `admin_router.py:5701-5711`) while the sidebar tooltip promises *"Directly modify a session's KPIs (Treasury, Reputation, Synergy) with absolute or delta values"* (`sidebarConfig.js:127`). A super-admin can even register a custom override ID (`admin_router.py:7934`) that then 400s at apply time. **[F]**
  - **There is no "submit on this team's behalf"** distinct from force-advance's auto-commit, and no "reopen a closed round" distinct from undo (which deletes rather than reopens). **[F]**

### Recoverability — **Critical gap**
- **The Manual-mode advance control is broken.** `RoundPacingControl.js:166` POSTs to `/api/admin/sessions/{id}/unlock-next`. That route **does not exist** — the backend implements `/api/admin/sessions/{id}/pacing/unlock` (`admin_router.py:3567`), and **nothing in the frontend calls it** (`grep -rn "pacing/unlock" frontend/` → zero hits). The facilitator sees "❌ Unlock failed". **[F]** This is in both the facilitator dashboard (`admin/facilitator/page.js:973`) and God Mode (`admin/god-mode/page.js:646`). Manual pacing is documented as *"the next round opens only when you advance it"* — and the only control that advances it is dead.
- **Advance is asymmetric with undo.** Unlock requires `require_sim_manager` (level ≥1) and has **no confirmation**; undo requires `require_lead_facilitator` (level ≥2) and lives in a different sidebar *category*. A base facilitator who over-advances **cannot fix it themselves** — they must escalate mid-session. **[F]**
- `unlock_next_round` does `pacing["unlocked_round"] + 1` with no upper bound and **no inverse endpoint** (`admin_router.py:3571`; the only decrements anywhere are `max(…, 1)` clamps). Unlocking is a one-way ratchet. **[F]**
- Undo itself **deletes** state and the audit rows behind the immutability triggers (`database.py:1372-1393`), is not recorded in the god-mode audit log (contrast `admin_god_controls.py:68` which does audit freeze/unfreeze), and its own copy says "This cannot be undone" (`UndoRound.js:52-56`). **[F]**
- **The restart landmine [F].** `_session_players` is a process-local `{}` (`router.py:122`) rebuilt only inside `join_session` (`:686-700`). After a backend restart it is empty until every player logs in again. Everything that iterates it silently no-ops: the X/Y committed badge (`_cohort_commit_progress` returns `(None, None)`), the wait-for-all barrier, and `_auto_commit_laggards` — so **Force Advance appears to succeed and advances nobody**. In memory mode the backend restarts more readily than in Postgres mode. This is the single most dangerous unhappy path in the product.
- Good precedent that should be copied: cohort deletion has a proper tiered confirm with blast-radius preview and 7-day soft delete (`admin/facilitator/page.js:753-791`).

### Cognitive load while facilitating — **Weak**
- **33 sidebar tabs across 5 categories, plus 3 external full-screen consoles = 36 navigable surfaces from one screen** (`config/sidebarConfig.js:94-170`, `admin/facilitator/page.js:1449-1503`). `platform_analytics` fans out into 7 sub-tabs. **[F]**
- No live-round mode. The tab a facilitator needs during a round sits in the same flat list as `technical_glossary` and `teaching_journal`.
- **10 of 11 facilitator visibility toggles are inert.** `EXTENDED_VISIBILITY_CARDS` (`analyticsRegistry.js:42-58`) exposes 11 keys in cohort setup; only `cohort_pulse` is consumed anywhere (`admin/facilitator/page.js:1182`). Verified: `isFacilitatorVisible('cohort_pulse')` is the only such call in the file. **[F]** Configuring the other ten does nothing — a direct violation of the repo's own CLAUDE.md tooltip-accuracy rule.

### Projection / presentation mode — **Weak**
- Three purpose-built full-screen pages exist (`admin/trading-floor`, `admin/war-map`, `admin/shockwave`) — genuinely good instinct. **[F]**
- But they are sized for a monitor, not a room: trading floor team names at 1.1 rem, rank at 1.4 rem (`trading-floor/page.js:329-346`); war-map SVG labels default to **10 px** (`war-map/page.js:26`). At the back of a 40-person room these are unreadable. **[F]**
- None of them shows *round state or commit progress* — the one thing a room screen should show.

### Debrief support — **Adequate**
- `DebriefReport.js` gives KPI trajectory charts, a consequence-DNA Sankey, and TCFD views; `dna_comparison` and `cohort_comparison` give cross-team views. **[F]**
- But the best narrative asset in the codebase — `MirrorDebrief.js`'s counterfactual "your biggest missed lever", with a hand-curated `MR_OPPORTUNITIES` catalog per round and option (`:31-50`) — is **player-only**, mounted in `GameOverSummary.js:211`. The facilitator never sees it and cannot get the room-level version of it. **[F]**
- Net: the product hands the facilitator dashboards and wishes them luck assembling the story live.

### Post-run — **Adequate**
- CSV and JSON export (`ReportsExport.js:224-246`). The sidebar tooltip promises "CSV/PDF" (`sidebarConfig.js:147`); **there is no PDF path** in that component. **[F]**
- Grading support exists (`StudentBonuses.js`, `PeerEvaluation.js`); no LMS integration. **[F]**
- Re-running with a new cohort is supported as a **settings template** (`POST /api/admin/cohort-templates`, applied at create time) — good, and under-surfaced in the UI. **[F]**

### Scale — **Weak**
- Roster ceiling 20 (`player_capacity.MAX_PLAYERS_CEILING`), legacy default 5 — and `admin_shared.py:734-745` documents a shipped bug where `max_players` was silently inert. At the stated 15–20 cohort size you are operating at the ceiling. **[F]**
- Concurrent cohorts per facilitator capped at 5 by default (`admin_router.py:310`). **[F]**
- **No co-facilitator or TA.** Ownership is single-facilitator, enforced by `_assert_session_ownership` (`admin_router.py:122-141`) with no multi-owner list; only super_admin/god_mode see across. A `lead_facilitator` gets more *tools*, not more *visibility*. **[F]** For a university course with a TA, or an exec workshop with a co-facilitator, the only workaround the repo documents is credential sharing.

### Trust & observability — **Weak**
- A "● Live / ⟳ Reconnecting" pill and a 50-entry in-memory feed explicitly labelled non-durable (`admin/facilitator/page.js:1211-1224, 1561-1573`). **[F]**
- Everything else that would answer "is the system healthy" is God-Mode-only. A facilitator's first signal that something is wrong is a participant raising their hand.
- Footnote **[F]**: `GET /api/admin/cohort-pulse/{id}` (`admin_router.py:10739`) has **no auth dependency** — no `require_*` guard, and `admin_router` has no router-level dependency (`:266`). The client comment at `CohortPulse.js:44-46` asserts it is guarded. Out of scope for UX, but you should know.

---

## 5. Cross-cutting

**Consistency between surfaces — Weak.** The player cockpit and the facilitator dashboard share no primitives. **There is no component library at all** — no `Button`, `Modal`, `Card`, `Input`; 54 files define their own `.card*`, 26 their own `.overlay*`, 10 their own `.modal*`; 624 `<button>` elements with no wrapper; 6 independent bespoke toast implementations. **[F]**

**Design-system maturity — Weak.** Four overlapping token vocabularies (`tokens.css`, the `globals.css` core set, the `globals.css` "Phase G ESG" set, per-component `--ck-*`), three unreconciled type scales, two spacing naming conventions. Measured drift across `components/*.module.css`: **1,242 raw hex occurrences, 4,887 raw px, 1,762 font-size declarations across 108 distinct values, 363 box-shadows across 293 distinct values.** Token usage for margin/padding is 14%. `globals.css:112-120` declares a 9-tier z-index scale topping out at 9000; component CSS reaches 21500 and inline JS reaches `2147483647`. **[F]** `globals.css:1036-1210` is an entire "Light Mode — Inline Style Color Compatibility Shim" that overrides React's serialized `style*="color: rgb(...)"` strings — the debt is already being paid in the ugliest possible currency.

**Performance & perceived latency — Adequate.** ~15 uncoordinated polling loops per tab. Functionally fine at this scale; the *perceived* latency problem is elsewhere (the missing in-flight commit state).

**Empty / loading / error states — Weak.** One real skeleton implementation in the entire app (`EngineWidgetsPanel.js:94-100`) despite `globals.css:599-631` shipping a full skeleton utility set; zero `Spinner` components; 6 files rendering a bare `Loading...` string; `FullScreenLoader` (`page.js:20`) is an **empty unlabelled div** — a slow chunk load is a black screen. `sim.loading` is tracked and never rendered. Good empty states do exist (`PeerComparison.js:212`, `DebriefReport.js:598-604` — the latter tells you how to unlock the content, exactly right). **[F]**

---

## 6. Prioritized recommendations

Ranked by learning-outcome and run-day impact per unit of engineering effort. Effort: XS ≤ half day · S ≤ 2 days · M ≤ 1 week · L > 1 week.

| # | Recommendation | Surface | Problem it solves (evidence) | Impact | Effort | Sim-logic risk | Files / components |
|---|---|---|---|---|---|---|---|
| 1 | Fix the dead Manual-mode advance button | Fac | `RoundPacingControl.js:166` calls `/unlock-next`, which does not exist; backend route is `/pacing/unlock` (`admin_router.py:3567`) and has **zero** frontend callers. Manual pacing has no working advance control. | Critical | XS | None | `RoundPacingControl.js` |
| 2 | Commit-status column + cohort progress strip in the facilitator view | Fac | Players see "3/5 committed"; the facilitator cannot. `cohort-pulse` already returns `round` per team (`admin_router.py:10820`) and the client discards it (`CohortPulse.js` has no `round` render). | Critical | S | None | `CohortPulse.js/.module.css`, `admin/facilitator/page.js` |
| 3 | Rebuild `_session_players` at startup | Fac | Process-local dict (`router.py:122`) empty after restart ⇒ X/Y badge, wait-for-all barrier and **Force Advance all silently no-op**. Rebuild code already exists inline at `router.py:688-700`. | Critical | S | ⚠️ see §7.3 | `backend/router.py`, `backend/main.py` |
| 4 | Validate before you confirm (player commit gates) | Player | `attemptCommitTurn` (`page.js:1281-1313`) runs the stakeholder-map / matrix / quiz / side-track gates **after** the review modal's "Confirm & Commit". | High | S | None | `page.js`, `ExecutiveCockpit.js` |
| 5 | Real in-flight commit state; retire the fake ceremony | Player | 800 ms animation runs *before* the POST (`page.js:1307-1312`); `sim.loading` never read in `page.js`. Slow commit = dead UI. | High | XS | None | `page.js`, `ExecutiveCockpit.js`, `useSimulation.js` |
| 6 | Confirm + inverse on round unlock; move Undo next to Advance | Fac | Unlock has no confirm and no inverse (`admin_router.py:3571`); undo needs a higher role and a different sidebar category (`sidebarConfig.js:110-168`). | High | S | ⚠️ see §7.6 | `RoundPacingControl.js`, `admin_router.py`, `sidebarConfig.js` |
| 7 | Retire the "team" fiction (confirmed: one login per person) | Player+Fac | Players are individuals (`router.py:649-651` + your §11 Q2 answer), yet copy says "teams" and `team_consensus: 'majority'` is fabricated into the audit log (`page.js:788`); concurrent same-login editing unguarded. | High | S | None | `JoinCohortModal.js`, `ExecutiveCockpit.js`, `CohortPulse.js`, `PlayerRegistry.js` |
| 8 | Keyboard-operable decision tiles | Player | `<div onClick>` with no role/tabIndex/key handler on the core decision (`ExecutiveCockpit.js:1804-1808`). WCAG 2.1.1 failure on the primary interaction. | High | S | None | `ExecutiveCockpit.js` + `.module.css` |
| 9 | Persistent auto-commit disclosure | Player | Server auto-commits with `option_b` + `$1`/BU (`router.py:254-263`); client shows a toast that vanishes in 5 s (`page.js:1728-1745`) and never says what was submitted. | High | S | None | `page.js`, `ExecutiveCockpit.js` results overlay |
| 10 | Objective statement + persisted onboarding | Player | No statement of what you optimise for in the first 5 min (`OnboardingWalkthrough.js:16`); tour and briefing replay on every refresh (`page.js:430-435`). | High | S | None | `RoundBriefing.js`, `OnboardingWalkthrough.js`, `page.js` |
| 11 | Fix light-mode KPI contrast | Both | `--kpi-good` 3.44–3.77:1, `--kpi-warn` 2.91–3.19:1 — fail AA, against a comment claiming 4.5:1+ (`globals.css:149-150`). | Med-High | XS | None | `globals.css` |
| 12 | Facilitator-side Mirror Debrief roll-up | Fac | `MirrorDebrief.js` counterfactual analysis is player-only (`GameOverSummary.js:211`); facilitator gets charts, not a story. | High | M | None | `MirrorDebrief.js`, `DebriefReport.js`, new admin endpoint |
| 13 | Live-round mode for the facilitator sidebar | Fac | 33 tabs + 3 consoles (`sidebarConfig.js:94-170`) with no during-a-round subset. | Med-High | M | None | `sidebarConfig.js`, `admin/facilitator/page.js` |
| 14 | Room-legible projector typography + round state on the big screen | Fac | 10 px SVG labels (`war-map/page.js:26`); no round/commit state on any projector page. | Med | S | None | `admin/war-map`, `admin/trading-floor` |
| 15 | Make the timer honest (or hide it honestly) | Player | Timer returns `null` in `free` mode (`DecisionPressureTimer.js:84`) and is occluded by every full-screen sub-flow. | Med | S | None | `DecisionPressureTimer.js`, `page.js` |
| 16 | Delete or implement the 10 inert visibility toggles | Fac | `EXTENDED_VISIBILITY_CARDS` has 11 keys; only `cohort_pulse` is consumed. | Med | XS (delete) / L (implement) | None | `analyticsRegistry.js`, `CreateCohortModal.js` |
| 17 | Truth-up the tooltips | Fac | Manual override "absolute or delta KPI values" vs 3 hardcoded events; "CSV/PDF" with no PDF; "connection status" that is never rendered. | Med | XS | None | `sidebarConfig.js`, `analyticsRegistry.js` |
| 18 | Extract `ConfirmModal` into the one dialog primitive | Both | 6 of 8 modals lack dialog semantics, Escape and focus management; `ConfirmModal.js` already has most of it. | Med | M | None | `ConfirmModal.js`, 7 modal components |
| 19 | Staged cohort creation with a pre-lock preview | Fac | 84 `useState`, 11 sequential calls, partial-failure repair panel (`CreateCohortModal.js:682-1092`), 2 validated fields. | Med | L | None | `CreateCohortModal.js` |
| 20 | Token consolidation, incrementally | Both | 4 vocabularies, 293 distinct shadows, 108 font sizes, z-index to 2147483647. | Med | L | None | `tokens.css`, `globals.css`, all `*.module.css` |
| 21 | Complete the consequence chain | Player | `ConsequenceReplay.js:28-98` is built from a hardcoded event-key list; unlisted engine effects vanish from the explanation. | High | M | ⚠️ read-only over engine output | `ConsequenceReplay.js` |
| 22 | Co-facilitator / TA read access | Fac | Single-owner enforcement (`admin_router.py:122-141`); no multi-owner list. | Med | L | None | `admin_shared.py`, `admin_router.py`, `sidebarConfig.js` |

---

## 7. Detailed specs — top 8

### 7.1 Fix the dead Manual-mode advance button

**Current [F].** `RoundPacingControl.js:162-181` `unlockNext()` POSTs `${API}/api/admin/sessions/${sessionId}/unlock-next`. No such route exists in `backend/admin_router.py`. The implemented route is `POST /api/admin/sessions/{session_id}/pacing/unlock` (`admin_router.py:3567`), which has zero callers anywhere in `frontend/`. The button renders only when `mode === 'manual'` (`:392`) and reports "❌ Unlock failed" on a 404. The same broken component is mounted in the facilitator dashboard (`admin/facilitator/page.js:973`) and God Mode (`admin/god-mode/page.js:646`).

**Proposed.** Point `unlockNext` at `/pacing/unlock`. Add `credentials: 'include'` for consistency with `forceAdvance` (`:189`) — currently harmless because `next.config.mjs` rewrites `/api/*` to the backend so requests are same-origin, but the inconsistency is a trap the day someone sets an absolute API URL.

**Interaction detail.**
- Success: optimistic `unlocked_round` update, toast `✅ Round {n} unlocked — teams can now commit Round {n}`.
- 403 (`require_sim_manager` / ownership): `You do not have permission to advance this cohort.` — not the generic "Unlock failed".
- 409/network: leave `unlocked_round` unchanged, offer Retry.
- Add a bound: disable at `unlocked_round >= 10` with copy `All rounds unlocked`.

**Why this over the obvious alternative.** The alternative is adding an `/unlock-next` alias server-side. Don't: it enshrines a second name for one transition and the pacing surface already has enough drift. Fix the caller.

**Verification of sim equivalence.** This touches pacing policy only, never `engine.process_tick`. Run `pytest backend/tests/test_simulation_integrity.py backend/tests/test_stakeholder_golden_trace.py backend/tests/test_facilitator_paced_advance.py` — all should pass unchanged. Manual check: set a 2-team cohort to Manual, press Unlock, assert `GET /pacing` shows `unlocked_round` incremented by exactly 1 and both teams' commit gate opens for exactly that round.

---

### 7.2 Commit-status column + cohort progress strip (the control room fix)

**Current [F].** `CohortPulse.js` polls `/api/admin/cohort-pulse/{id}` every 15 s and renders a KPI heatmap. The response already contains `round` per team (`admin_router.py:10820`) and `total_teams`; the client never reads `round`. Meanwhile `_cohort_commit_progress` (`router.py:185`) computes the exact "committed vs target round" tally and injects it into **player** dashboards only.

**Proposed.** Two additive changes, no new backend logic.

1. **Extend `/cohort-pulse` response** with the fields it already has in hand: per team `{ round, committed: bool, last_commit_at }` where `committed = (round >= max(all rounds))` — i.e. lift `_cohort_commit_progress`'s existing rule into the pulse serializer. Add cohort-level `{ target_round, committed_count, total_teams, pacing_mode, unlocked_round, next_unlock_at }` by reading `admin_shared._get_pacing`.
2. **Render a persistent Cohort Strip** above the heatmap and pinned in the facilitator dashboard header, independent of which tab is open:

```
Round 4  ·  ●●●○○  3 of 5 committed  ·  opens 14:35  ·  ⟳ 6s ago
Team B — Round 3, no draft saved, 11 min idle          [Nudge] [View]
```

**Interaction detail.**
- Team row states: `Committed` (solid) · `In progress — draft saved 2 min ago` (pulsing) · `No draft, N min idle` (amber) · `Never joined` (grey). Derive idle from `last_commit_at` and draft presence (`saved_round`); **[A]** if `saved_at` is not persisted, add it as a metadata field — additive, not sim state.
- Poll at 5 s during a live round (matching `DecisionPressureTimer`), 15 s otherwise.
- Colour is never the only signal: shape + text label on every state (WCAG 1.4.1).
- Clicking a team opens the existing `session_viewer`, not a new surface.

**Why this over the obvious alternative.** The obvious alternative is a new "Control Room" page. Resist it — a new tab is a 34th tab. The value is *persistence*: the strip must be visible while the facilitator is in Broadcast, Swipe File, or Teleprompter. Build it as a header region of `admin/facilitator/page.js`, not a tab.

**Verification.** Read-only over data the engine already produced. `pytest backend/tests/test_mp_commit_indicator.py` pins the badge semantics; assert the new admin field equals the player-side `team_commits_this_round` for the same cohort at the same instant. No engine test should move.

---

### 7.3 Rebuild `_session_players` at startup ⚠️ TOUCHES SIM-ADJACENT LOGIC

**Current [F].** `_session_players: dict = {}` (`router.py:122`) is process-local and populated only when a player calls `join_session` (`:906`), with a rebuild-from-persisted-sub-sessions block that runs **only inside that same handler** (`:688-700`). Consumers: `_cohort_commit_progress` (`:197`), `_auto_commit_laggards` (`:281`), `_cohort_advance_status` (`:318`), and `admin_router.py:3279, 7748`.

**Failure mode.** Backend restarts mid-session (routine in memory mode). Until every player re-logs in: the X/Y badge disappears; the wait-for-all barrier silently lifts (`_cohort_commit_progress` → `(None, None)` → `teamCount = 0` → `isMultiTeam` false); and **Force Advance returns `{"status":"ok"}` while `_auto_commit_laggards` iterates an empty list and advances nobody.** The facilitator gets a success message and nothing happens.

**Proposed.** Hoist the existing rebuild block into a module-level `rebuild_session_players()` and call it (a) once on FastAPI startup after the DB backend is selected, and (b) as a lazy self-heal at the top of `_cohort_commit_progress` and `_auto_commit_laggards` when the sibling list is empty but `parent_cohort_id` is set.

**What changes and how to verify equivalence.** This changes **which sessions are visible to the cohort barrier**, which changes *when* rounds advance — that is why it carries the ⚠️. It does **not** change `process_tick`, scoring, or any per-round math. Verify:
1. `pytest backend/tests/` in full — `test_simulation_integrity.py`, `test_stakeholder_golden_trace.py`, `test_mp_commit_indicator.py`, `test_facilitator_paced_advance.py`, `test_concurrent_commit_race.py` must all pass unmodified.
2. New test: create a 3-team cohort, commit 2 teams, **clear `_session_players`** to simulate a restart, call the rebuild, assert `_cohort_commit_progress` returns `(2, 3)` — identical to the pre-clear value.
3. New test: same setup, press Force Advance, assert `_auto_commit_laggards` returns 1 and the third team's round advanced by exactly 1 with `option_b` / `$1` per BU (the documented fallback), and that `db.fetch_latest_state` for the two already-committed teams is byte-identical before and after.

**Why this over the obvious alternative.** The alternative is moving `_session_players` into the durable store. That is the right long-term answer and it is a larger change with a Postgres-parity surface (see the repo's own `AUDIT_guards_and_memory_stores.md`). The rebuild is the same behaviour for one day of work and blocks the run-day failure now.

---

### 7.4 Validate before you confirm

**Current [F].** The footer commit button (`ExecutiveCockpit.js:3505-3517`) and the allocation-stage button (`:1968-1982`) both check only *"decision selected"* and *"allocation > 0"*, then open the prediction modal. The modal's "✓ Confirm & Commit" calls `onCommit` → `page.js:1647` → `attemptCommitTurn` (`page.js:1281`), which only then checks the side-track block, the R1 stakeholder-map gate, the R2 materiality gate and the quiz gate — surfacing a `blockAlert` modal whose only action is "Understood". The player has reviewed, confirmed, and is then refused.

**Proposed.** Compute a single `commitReadiness` object at the button-render level and drive all three surfaces from it.

```js
// { ready: bool, blockers: [{ id, label, cta, onAction }] }
```
Blockers, in the order they should be resolved: `side_track` · `stakeholder_map` (R1) · `materiality_matrix` (R2) · `quiz_gate` · `no_decision` · `no_allocation` · `round_locked`.

**Interaction detail.**
- With blockers, the commit button renders disabled with the **first** blocker's label and a working CTA — this pattern already exists for two of the seven (`🧩 Complete the Quiz First`, `🔒 Round Locked — opens 14:35`, `ExecutiveCockpit.js:3450-3495`). Extend it to all seven rather than inventing anything.
- Below the button, a compact checklist of remaining blockers, each row clickable to the surface that resolves it (Resources for the quiz, ⚖️ Stakeholder Map, etc.). Reuse the `DebriefReport.js:598-604` empty-state pattern: state the unlock condition, don't just refuse.
- The prediction modal becomes reachable **only** when `ready === true`, so it never needs to refuse. Keep `attemptCommitTurn`'s server-mirroring checks as a defensive backstop — just make them unreachable in normal play.
- Rename the modal actions to remove the misclick trap: `Go back` (tertiary, left) · `Commit without predicting` (secondary) · `Commit decisions` (primary, visually dominant, right). Drop "Skip &" — the word "Skip" adjacent to an irreversible commit is the problem. **[F]** Both current escape and commit actions share the `.predictionSkip` class (`ExecutiveCockpit.js:3772-3783`).

**Why this over the obvious alternative.** The alternative is adding a second confirm step. The repo already retired one duplicate confirm deliberately (`page.js:1770-1772`) and was right to. The fix is ordering, not more ceremony.

**Verification.** Purely client-side gating; the server gates in `_commit_turn_impl` (`router.py:1956-2000`) are untouched and remain authoritative. Assert via the existing e2e (`backend/test_e2e_full_flow.py`) that a commit which previously succeeded still succeeds with an identical request payload.

---

### 7.5 Real in-flight commit state

**Current [F].** `attemptCommitTurn` sets `showCommitCeremony(true)`, waits a fixed `setTimeout(…, 800)`, sets it **false**, and only then calls `handleCommitTurn()` — the actual POST (`page.js:1307-1312`). `useSimulation` maintains a `loading` flag across 9 call sites; `page.js` destructures `sim` but never reads `sim.loading`. There is no spinner, no disabled state, no timeout copy during the request.

**Proposed.**
- Delete the pre-request `setTimeout`. Call `handleCommitTurn()` immediately.
- Keep the ceremony visual, but bind its lifetime to the request: mount on request start, hold for `max(800ms, requestDuration)`, dismiss on resolution. The ceremony now *means* something.
- Copy ladder by elapsed time: 0–2 s `Committing your decisions…` · 2–6 s `Still working — the room is busy.` · >6 s `This is taking longer than usual.` + a **Cancel and retry** action.
- On failure, replace the small bottom toast (`page.js:1941-1948`) with an inline recovery card in the commit area: `Your decisions were not committed. Nothing was lost.` + Retry. **[F]** This matters because the current failure state leaves the player unable to tell whether the round advanced.
- Add `aria-live="polite"` to the status region.

**Why this over the obvious alternative.** The alternative is a global loading overlay. Don't — during a timed round, blanking the screen removes the timer and the allocation state the player is anxious about. Keep it local to the commit control.

**Verification.** No request shape changes; only client sequencing. Existing commit tests unaffected. Manual: throttle to Slow 3G, confirm the button never returns to an idle-looking state while a request is in flight, and that a forced 500 leaves `allocations`/`decisionChoice` intact and re-committable.

---

### 7.6 Confirm + inverse on round unlock; co-locate Undo ⚠️ TOUCHES PACING STATE

**Current [F].** `unlock_next_round` does `pacing["unlocked_round"] = pacing["unlocked_round"] + 1` with no bound and no inverse (`admin_router.py:3571`). The only writes that lower it are `max(…, 1)` clamps in `set_pacing`. Guard is `require_sim_manager` (level ≥ 1). Undo Round is `require_lead_facilitator` (level ≥ 2, `admin_router.py:8483`) and sits in the "Configuration" sidebar category while pacing sits in "Live Classroom" (`sidebarConfig.js:110-168`). Force-advance uses a native `window.confirm` (`RoundPacingControl.js:185`) while the app has a proper `ConfirmModal`.

**Proposed.**
1. **Confirm with blast radius.** Replace `window.confirm` and add a confirm to unlock, both using `ConfirmModal`: *"Open Round 5 for all 5 teams? 2 teams have not committed Round 4 — they will keep their Round 4 window open."* Show the live commit tally from 7.2 inside the dialog. This is the moment the facilitator most needs the room state, and it is the moment they currently have least of it.
2. **Add `POST /sessions/{id}/pacing/relock`** — decrement `unlocked_round` by 1, floored at the highest round any team has actually committed (never strand a team mid-round). Surface it as an **inline "Undo — relock Round 5" affordance that appears for 60 s after an unlock**, in the same button row. Not a new tab.
3. **Promote Undo Round into the Live Classroom category** and render it (disabled, with the reason) for base facilitators so the escalation path is discoverable rather than invisible.

**Interaction detail.** Relock copy must be honest about what it does not do: *"This closes the Round 5 window. Teams that already committed Round 5 keep their results — use Undo Round to roll those back."* Undo remains the heavier, lead-facilitator tool.

**Why this over the obvious alternative.** The alternative — a full transactional round state machine with proper reversibility — is the right answer and is 7.8-class work. Relock is a one-field inverse of a one-field increment, and it converts the highest-stakes moment in the product from unrecoverable to recoverable for the common case (unlocked one too early, nobody has committed yet).

**⚠️ What changes.** `unlocked_round` gates commit eligibility in `_commit_turn_impl` (`router.py:1956-1970`). Lowering it can turn an allowed commit into a 403. **Verify:** (a) relock must refuse when `any(team.round > target)` — assert with a 3-team fixture where one team has advanced; (b) `pytest backend/tests/test_facilitator_paced_advance.py backend/tests/test_simulation_integrity.py backend/tests/test_stakeholder_golden_trace.py` unchanged; (c) assert no round state row is created or deleted by relock — `db.fetch_round_history` byte-identical before and after.

---

### 7.7 Retire the "team" fiction *(revised after your answer to §11 Q2: one login per person)*

**Current [F].** One player ID = one independent session with its own game state (`router.py:648-651`) — and you have confirmed that is also how it is used: every participant is their own company. Yet the product speaks team throughout: `team_consensus: 'majority'` is a hardcoded literal in every commit payload (`page.js:788`) with no team behind it; the post-commit barrier says "Waiting for Other **Teams** — X/Y **teams** committed" (`ExecutiveCockpit.js:4337-4353`); `CohortPulse` is billed as a *team* KPI heatmap. Separately: two browsers on the same credentials can still edit concurrently — now meaning one *person* on a laptop and a phone — with only a per-tab ref as guard (`useSimulation.js:401-405`), and the join screen's "REMEMBER STATION" checkbox is an unbound `<input type="checkbox">` with no state (`JoinCohortModal.js:142-145`) — dead UI on the first screen a participant ever sees.

**Proposed.**
1. **Rename the vocabulary to match reality.** "Teams" → "players" (or "companies") in the barrier copy, the commit badge, CohortPulse labels and the leaderboard. This is find-and-replace-with-eyes-on-screen work, and it removes a standing lie from the most emotionally loaded screens in the product. Delete the dead checkbox while you are in `JoinCohortModal.js`.
2. **Stop fabricating `team_consensus`.** It is a DB enum (`db/init.sql:91-105`) being written as `'majority'` into a graded, immutable audit log for decisions no team made. Omit it (make the field nullable in the payload) rather than inventing a selector — with individual players there is no consensus to record. Keep `facilitator_override` for the one case that is real.
3. **Second-session detection still stands**, reframed: when the dashboard poll (already running at 5 s) detects a newer `ws_ticket`/heartbeat for the same player ID, show a non-blocking banner on the older tab: *"Your account is also open on another device. Only one screen should commit."* Requires one additive field — last-seen device token per player — no sim state. **[I]** The WS ticket infrastructure at `useSimulation.js:366-374` already carries what's needed.
4. **If you want team deliberation pedagogically, make it a facilitation pattern, not a feature** — e.g. a cohort setting that groups players into named discussion pods shown on the facilitator roster and debrief, while each still commits their own company. That records the social structure without touching the one-session-per-login architecture.

**Why this over the obvious alternative.** The alternative is building actual shared team sessions — a shared session model, a conflict strategy, and a rewrite of the commit path; weeks of work against a validated engine, and your confirmed usage doesn't need it. The damage today is done by words and fabricated data, both cheap to fix.

**Verification.** Grep `team_consensus` in `backend/engine.py` and `round_logic.py` to confirm zero reads (it is audit-log-only), then assert the golden trace is unchanged with the field omitted. The rename is copy-only; no request shape or engine input changes beyond dropping the fabricated field.

---

### 7.8 Persistent auto-commit disclosure

**Current [F].** When a round is auto-committed, `_auto_commit_request` (`router.py:248-273`) uses the team's saved draft, or falls back to `choice = "option_b"` and `capex = max(1.0, alloc)` — **$1 per BU**. The client detects it on the 5 s poll and shows a banner that auto-dismisses after 5 s (`page.js:1728-1745`): *"⏰ Time expired — your turn was auto-committed with default choices."* Nothing tells the player, or later the facilitator, what was actually submitted.

**Why this matters more than it looks.** In classroom mode this is a graded artifact. A student who steps out gets a round submitted in their name, with a near-null investment, and the only notice evaporates in five seconds. In the debrief, that round's data is indistinguishable from a deliberate conservative strategy.

**Proposed.**
1. **Results-stage disclosure card**, persistent (not a toast), rendered whenever `active_event_flags.auto_committed` is true, in the results stage — consistent with the repo's own rule that retrospective content renders in the results stage (CLAUDE.md V-A):
   > **This round was submitted for you.** The round closed before you committed. We submitted: Option B, $1 to each business unit. Your results below reflect that.
   Or, when a draft existed: *"…your last saved draft: Option A, $12M Pharma / $8M Electronics."*
2. **Mark it in history.** An `Auto` chip on that round in the round timeline and in `DebriefReport`/`ReportsExport` output, so the facilitator and any grading reflect it.
3. **Facilitator-side count** in the cohort strip from 7.2: `Round 4 · 2 teams auto-committed`.

**Interaction detail.** Tone matters: state what happened, not what the player did wrong. No red. Use the caution token, not the danger token.

**Why this over the obvious alternative.** The alternative is changing the fallback (e.g. commit nothing, or hold the round open). That is sim-behaviour and out of bounds. Disclosure is purely additive over a flag the engine already sets.

**Verification.** Read-only over `active_event_flags.auto_committed` and the persisted decision. Assert `pytest backend/tests/test_simulation_integrity.py backend/tests/test_stakeholder_golden_trace.py` unchanged, and that a normal (non-auto) commit never renders the card.

---

## 8. Now / Next / Later / Don't

### Now — ship this sprint
| | |
|---|---|
| **1** Fix the dead unlock button — **release blocker** now that Manual pacing is confirmed (§11 Q1) | XS, none |
| **5** Real in-flight commit state | XS, none |
| **11** Light-mode KPI contrast | XS, none |
| **17** Truth-up the lying tooltips | XS, none |
| **16a** Delete the 10 inert visibility toggles | XS, none |
| **2** Cohort commit strip | S, none |
| **3** Rebuild `_session_players` | S, ⚠️ verified per 7.3 |
| **4** Validate before confirm | S, none |
| **8** Keyboard-operable decision tiles | S, none |
| **9** Auto-commit disclosure | S, none |

That is roughly two engineer-weeks and it changes the run-day character of the product more than anything else on this list.

### Next — needs design or spec time
*(order revised per your §11 answers)*
- **6** Unlock confirm + relock inverse + Undo co-location — **first in this bucket**: the accidental-advance-with-diverged-players incident you described (§11 Q6) is exactly this, and prevention must include a divergence warning in the cohort strip
- **18** One dialog primitive extracted from `ConfirmModal` + modal accessibility sweep — **promoted: WCAG conformance is contractual** (§11 Q7); plan a full conformance pass (audit → fix → VPAT) as its own workstream
- **22** Co-facilitator read-only observer access — **promoted from Later** (§11 Q8: a co-facilitator is in the room, currently on shared credentials)
- **12** Facilitator-side Mirror Debrief roll-up — **promoted from Later** (§11 Q5: the debrief is spoken by the facilitator, so this feeds exactly what is done manually today); start with the 3-day prediction-persistence seed in the Now sprint, and build each section projectable full-screen (see #14)
- **14** Projector legibility + a projectable debrief view — **restored to Next** (§11 Q5 revised: a projector is needed and some debrief is projected); primary surface is #12's debrief sections at room scale, secondary is fixing Trading Floor / War-Map type sizes
- **7** Retire the "team" fiction (rename copy, drop fabricated `team_consensus`, second-session banner)
- **10** Objective statement + persisted onboarding
- **15** Honest timer behaviour — focus on Timed-mode occlusion; the Free-mode null case is a non-issue for you (§11 Q3)
- **13** Live-round mode for the sidebar
- **21** Complete the consequence chain (drive it from the full engine event set, not a hardcoded key list)

### Later / bets
- **19** Staged cohort creation with a pre-lock preview and a single transactional create endpoint
- **20** Token consolidation, file by file, behind a CI drift check modelled on the existing `test_role_hierarchy_sync.py` tripwire
- Move `_session_players` and `_round_pacing` fully into durable storage
- Persist round state as an event log, which is the precondition for real undo/redo

### Don't
| Don't | Why |
|---|---|
| **Don't build real-time multiplayer team collaboration** (cursors, presence, co-editing) | The architecture is one independent session per login (`router.py:649-651`). This is a rebuild of the commit path against a validated engine, to solve a problem 7.7's copy-and-banner solves for 95% of cases. |
| **Don't do a big-bang token/colour sweep** | Your own CLAUDE.md says hue decisions happen on a real screen, never in a blind regex — and `globals.css:1036-1210` is the scar tissue from the last attempt. Consolidate per-file, with a tripwire. |
| **Don't add a PDF export because the tooltip promises one** | Fix the tooltip. `StudentReportExport.js:67`'s print-to-PDF already covers the real need. |
| **Don't build a new "Control Room" tab** | You have 33 tabs. The value of 7.2 is that it is *always visible*, not that it exists. A 34th tab is a regression. |
| **Don't rebuild the app in TypeScript now** | Tempting at 80k LOC of JS, and it would not move a single number in this audit. Do it incrementally at module boundaries, later, if at all. |
| **Don't add more confirmation steps to the player commit** | You already retired a duplicate confirm and were right to (`page.js:1770-1772`). The problem is ordering (7.4) and button hierarchy, not quantity. |
| **Don't make Undo Round reversible** | Redo over a destructive delete is a trap. Invest in *preventing* the bad advance (7.6) rather than reversing it twice. |
| **Don't extend the round to a submit-then-resolve two-phase model** to enable a proper waiting room | Commit == resolve is load-bearing across `_commit_turn_impl`, the concurrency stack and the golden trace. Fix the waiting *experience* (7.2, 8-Next) without touching the seam. |

---

## 9. Path to world class

The gap between where Muressons is and world class is not features. You have more features than any competitor I would expect in this category. The gap is that **the product is written for the player and the facilitator is running it blind.** Everything below follows from that.

### Borrow from live-event control surfaces (broadcast switchers, Ableton's session view, ATEM)

The defining idea of a switcher is **Preview / Program**: the operator always sees what is live *and* what is queued, and the transition between them is one deliberate, always-in-the-same-place action with a visible undo.

Muressons has the opposite: the state that matters (who has committed) is invisible, and the transition (unlock) is an unconfirmed increment with no inverse, sitting in a tab you have to navigate to.

**The move: a persistent Run Bar.** One horizontal strip, always mounted on the facilitator surface regardless of tab — round, commit tally, pacing mode, next unlock time, backend health, and exactly two actions: **Advance** (with blast radius in the confirm) and **Undo last action** (live for 60 s). Everything else stays a tab. This is 7.2 + 7.6 built as one thing.

**Cost:** ~1.5–2 engineer-weeks. It is the single highest-leverage investment in this document. A facilitator who has run Marketplace, Capsim or Cesim will notice it in the first thirty seconds, because none of them have it either.

### Borrow from the best learning products: the explanation is the product

Your endgame explanation quality is already excellent — `SustainabilityBalancedScorecard.js:256-267` writes causal English about M_R components; `MirrorDebrief.js:31-50` computes the counterfactual you should have taken. That is better than most of the category.

And it is delivered once, at the end, to the player, and never to the facilitator.

**The move: the debrief writes itself.** After a run, generate a facilitator-facing narrative from data you already compute: the round where teams diverged most (variance in the KPI vectors you already store per round), each team's largest missed lever (`MirrorDebrief`'s existing logic, run per team), the two decisions that best predicted final M_R, and the moments where a team's stated prediction (already captured in `sessionStorage` at `ExecutiveCockpit.js:3789` — persist it server-side instead) diverged from what happened. Ship it as an editable outline the facilitator opens on the projector.

That last one is the real prize. **You are already asking players to predict before they commit, and then throwing the prediction away into `sessionStorage`.** Predicted-vs-actual, aggregated across the room, is the single most powerful debrief artifact in management education, and you are three days of work from having it.

**Cost:** ~2–3 engineer-weeks for the roll-up, ~3 days for prediction persistence alone. Do the prediction persistence in the Now bucket; it is nearly free and it is the seed of everything else.

### Borrow from professional dashboards: one screen the room can read

Trading Floor and War-Map show the right instinct and the wrong scale — 10 px SVG labels and 1.1 rem team names. And neither shows round state, which is the one thing a room screen should show.

**The move: a real Projector view** — round, timer, commit tally as five big blocks, and one rotating "what just happened" card driven by the engine event feed you already produce. Type floor 24 px, contrast ≥ 7:1, no colour-only encoding, tested from 10 m.

**Cost:** ~1 week. Lower leverage than the first two, but it is what makes the product feel like a *room* product rather than a web app someone projected.

### What makes a facilitator say "this one is different"

Two things, and neither is a feature list:

1. **"I always knew what the room was doing."** No competing simulation gives a facilitator live per-team commit and stall state with a one-click recoverable advance. This is the Run Bar.
2. **"The debrief was already written."** Every competitor hands over a spreadsheet. Handing over the room's own predicted-vs-actual, with turning points and counterfactuals per team, is a different product.

Everything else in this audit is hygiene. Important hygiene — a dead advance button and a keyboard-inoperable core decision are not small — but hygiene. These two are the difference.

---

## 10. Assumptions I made

1. **[A]** Production runs one FastAPI process. If you run multiple workers, `_session_players` and `_round_pacing` are per-worker and several findings get worse, not better; `coordination_store.py` covers pacing but not `_session_players`.
2. ~~**[A]** Teams share one login on one screen.~~ **Resolved by you: one login per person.** Each participant runs their own company, so the architecture and the actual usage agree — what is wrong is the *vocabulary*. "Team", "Waiting for Other Teams" and the fabricated `team_consensus` value describe a model that does not exist in your deployments. 7.7 has been revised from "make the shared-login model explicit" to "retire the team fiction".
3. ~~**[A]** Free pacing is the default in practice.~~ **Resolved by you (§11 Q1/Q3): you run Manual and Timed, never Free.** Two consequences: the dead Manual unlock button (§7.1) is a release blocker, and the component's `'free'` default (`RoundPacingControl.js:60`) is a trap — a cohort whose pacing tab is never touched runs in the one mode you never use. Default new cohorts to Manual.
4. ~~**[A]** The 15–20 cohort size means ~4–5 teams of 3–4.~~ **Resolved by the answer to 2: it is 15–20 separate logins.** That puts you at the `MAX_PLAYERS_CEILING` of 20 with a `_cohort_commit_progress` helper whose docstring still says "capped at 5 players" and which does N sequential `fetch_latest_round` calls per dashboard poll per player — O(N²) polling across the cohort at your real size. This moves from "worth a look" to a concrete pre-scale item: memoise the tally per cohort with a 2–3 s TTL, or compute it once in the pacing store on commit.
5. **[A]** I did not run the application. Every finding is from source. Two — the dead unlock endpoint and the inert visibility toggles — I would want confirmed by a 5-minute click-through before you spend anything, though the code evidence is unambiguous.
6. **[A]** Screenshots and visual craft (spacing rhythm, typographic hierarchy as rendered) are outside what I could assess from source. The measured drift numbers in §5 predict inconsistency; they do not prove it looks bad.

---

## 11. What I needed from you — answered 2 Aug

1. **Manual pacing: yes, you will use it.** Then recommendation #1 (§7.1) is not a bug fix, it is a **release blocker** — the only control that advances a Manual-mode round 404s. Nothing else in this document matters until that button works. Fix and click-test it before the next session.
2. **One login per person.** Incorporated — see 7.7 ("Retire the team fiction"), §3, and assumptions 2/4. Standing follow-up: whether you want team deliberation as a recorded facilitation pattern (7.7 item 4).
3. **Both formats run Manual or Timed, facilitator's choice.** Good — this simplifies things. It means Free mode (with its wait-for-all barrier, auto-commit-from-drafts and null timer) is effectively an unused code path for you, so: (a) the timer fix (#15) should focus on Timed mode occlusion, not the Free-mode null case; (b) the auto-commit disclosure (#9 / §7.8) still matters because **Timed mode also auto-commits stragglers at unlock** (`admin_router.py:3293-3296`); (c) consider defaulting new cohorts to Manual instead of Free (`RoundPacingControl.js:60` defaults to `'free'`) so a facilitator who forgets the pacing tab doesn't silently get the mode you never use.
4. **Answered: class is served from the Railway deployment.** Context, in plain terms: the backend stores all game state either in a **PostgreSQL database** (survives restarts properly) or in an **in-memory store that snapshots to one JSON file** — the mode where §7.3's "Force Advance silently does nothing after a restart" bites hardest. The Railway/Docker entrypoint defaults to Postgres (`docker-start.sh`) **only if a Postgres service is attached**; without one it either refuses to boot or, with `ALLOW_MEMORY_DB_IN_PROD=true`, runs the memory store anyway — and your own `AUDIT_guards_and_memory_stores.md` records the deployment running in memory mode at the time of that audit [F]. **Verify before the next class (10 seconds): open `https://<your-railway-url>/health` — `"demo_mode": true` means memory mode.** If it is memory mode, one thing is *worse* on Railway than on a laptop: **[I]** Railway containers get a fresh filesystem on every redeploy and can be restarted by the platform (`railway.json` sets `restartPolicyType: ON_FAILURE`), so unless a persistent volume is mounted where `memory_snapshot.json` is written, a redeploy or crash-restart loses **all cohort state**, not just the §7.3 roster map. The durable fix is attaching Railway's Postgres service and setting `DATABASE_URL`; until then, treat §7.3 as Critical and add a pre-class check of `/health` to the run-day routine.
5. **Debrief is spoken by the facilitator — and a projector is needed, with some debrief content projected.** *(revised from your follow-up)* Two consequences. First, §9's facilitator-facing debrief narrative (item #12) stays high-value — it feeds the spoken debrief directly. Second, #14 stays in Next, not Later, and its scope sharpens: the projector surface that matters most is a **projectable debrief view** — the comparative trajectories, turning points and predicted-vs-actual cards from #12 rendered at room scale (type floor 24 px, ≥7:1 contrast) — with the existing Trading Floor / War-Map pages fixed for legibility as the in-round secondary. Build #12's output so each section can go full-screen individually; that makes the projector view a rendering mode of the debrief, not a separate product.
6. **The accidental advance happened, and players ended up at different stages.** That is the exact failure §7.6 targets, and your requirement — "that should be avoided" — sharpens the spec: prevention first (confirmation with live commit tally: *"2 players have not committed Round 4"*), then the 60-second relock window, and additionally a **divergence warning** in the cohort strip (§7.2) whenever players' round numbers differ by more than the unlock window allows. §7.6 moves from Next to the top of Next, immediately behind the Now bucket.
7. **WCAG conformance is contractual.** Then §3's accessibility findings are not quality debt, they are compliance exposure. Blockers as of today: keyboard-inoperable decision tiles (2.1.1, on the core interaction), light-mode KPI contrast (1.4.3), six modals with no dialog semantics/Escape/focus management (4.1.2, 2.4.3), and sub-24px touch targets (2.5.8). #8 and #11 stay in Now; #18 (dialog primitive + modal sweep) is promoted to Next with a deadline, and you should plan a proper conformance pass (audit → fix → VPAT/accessibility statement) as its own workstream — the findings here are what source reading can catch, not a full audit with AT testing.
8. **A co-facilitator can be in the room.** Item #22 moves from Later to Next. Today their only option is sharing the facilitator's credentials — which `must_change_password` and the single-owner model (`admin_router.py:122-141`) actively fight. The minimal version is **read-only observer access**: a second named account granted view of a cohort's pulse/strip and debrief, no interventions. That is much cheaper than full multi-owner and covers the actual room scenario.
9. **A team is available.** Then the full Now bucket (~2 engineer-weeks) fits one sprint. Suggested sequence: #1 first (blocker, half a day), then #3 and #2 together (they share the restart/tally plumbing), then #4/#5/#9 (the commit path, one owner), with #8/#11/#17/#16a parallelised. Add the 3-day prediction-persistence seed from §9 to this sprint — it is the cheapest piece of the debrief investment you just confirmed you need.

---

*Prepared from source; revised 2 Aug after the client's answers to §11. Every claim marked **[F]** carries a file and line reference; **[I]** marks an inference from code patterns; **[A]** marks something I could not determine from the repository.*
