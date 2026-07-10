# Muressons — UI/UX Review: God Mode & Facilitator Screens

*Owner-authorised review of your own project. Review and plan only — no code was changed. Focus: making both dashboards intuitive for a facilitator running a live session under time pressure. Simulation logic, scoring, and data flow are treated as immutable; every recommendation is a UI-layer change.*

**Severity key:** 🔴 **Blocks facilitator** (can mislead or stall a live session) · 🟠 **Slows facilitator** (extra clicks, hunting, uncertainty) · ⚪ **Cosmetic**

---

## 0. What I read (not inferred from screenshots)

- `frontend/app/admin/god-mode/page.js` (1,236 lines) and `admin/facilitator/page.js` (1,847 lines) — both are single-page tab routers: an `activeTab` string switches over ~25–30 imported panel components.
- `config/sidebarConfig.js` — shared nav definitions + `filterSidebarForRole` (3-tier RBAC mirror of `admin_shared.py`).
- Key panels: `GodModeStatus.js`, `SessionHealthDashboard.js`, `DashboardHome.js`, `RoundTimeline.js`, `ManualOverride.js`, `UndoRound.js`, `RoundPacingControl.js`, `LeaderboardMatrix.js` (selection path), `FacilitatorTeleprompter.js` (selector + data flow).
- Prior context: `SIMULATION_CONTEXT.md` (round configs, role hierarchy), `SESSION_SUMMARY_Fable5.md`, `REVIEW_Muressons_Fable5_v2.md` (this review does not repeat its security/engine findings).

**Architecture facts that drive the UX findings:**

1. **The leaderboard array is the de facto client-side session store.** Everything (round numbers, cohort names, selection targets) derives from it.
2. **Facilitator screen:** leaderboard is fetched **once on mount**; all subsequent refreshes are triggered by the admin WebSocket (`/api/admin/ws/admin`). There is **no polling fallback, no `onclose` handler, and no reconnect logic** (page.js:525–565, 584–600).
3. **God Mode screen:** three independent pollers on the default tab — `SystemContextBar` (15s), `GodModeStatus` (10s), `SessionHealthDashboard` (15s) — plus leaderboard every 30s. No shared store; the same numbers are fetched and rendered twice.
4. **Session targeting is fragmented:** `selectedSession` lives in page state (persisted to `localStorage` on the facilitator side), but it is set in only a few places (Leaderboard row click, Teleprompter's own dropdown, per-tab dropdowns in God Mode's Debrief/Sandbox), while ~12 tabs *consume* it.
5. Both screens mix CSS-module styling with large amounts of inline styles; some panels (Quiz, CEO Interview) hardcode a light palette inside the dark dashboard.

---

## 1. Screen maps

### 1.1 God Mode — hierarchy, controls, states

| Layer | Contents | States observed in code |
|---|---|---|
| Login gate | Facilitator-credential login, super-admin check | idle / loading / error / session-expired banner |
| `SystemContextBar` (sticky top) | Live cohorts, active players, "System Health" chip | **has no error state** — renders zeros + "Optimal" when fetch fails |
| Sidebar (5 collapsible groups) | 23 tabs + 2 external links (Trading Floor ↗, Shockwave ↗) | open/closed per group; Ctrl+1–5 exclusive-open; Ctrl+B → Session Controls |
| Default tab `system_overview` | `GodModeStatus` (status cards, **Emergency Freeze**, ~12 Pedagogical Scaffolding pills, ~17 System Engine pills, hardening intelligence, round distribution, recent audit) + `SessionHealthDashboard` (per-cohort health cards) | loading / retry-on-unreachable (GodModeStatus only) / frozen banner |
| Danger Zone tab | Targeted deletion table, Clear Orphans, **Factory Reset** (type-phrase + 15s countdown + cancel) | loading / empty ("No cohorts active") / countdown / result |
| Per-tab session pickers | Debrief, Regulatory Sandbox only | picker hidden entirely when leaderboard is empty |

### 1.2 Facilitator — hierarchy, controls, states

| Layer | Contents | States observed in code |
|---|---|---|
| Login gate + username prompt | same auth flow; full-screen username modal if unset | idle / loading / error / expired |
| Sidebar (4 groups, role-filtered) | 27 tabs via `FACILITATOR_SIDEBAR` + `allowed_tabs` | open/closed; Ctrl+1–4; Ctrl+B → Bulk Messaging |
| Scaffolding strip (Dashboard Home only) | read-only God-Mode feature pills + "SYSTEM FROZEN" chip | present only when `scaffolding-status` fetch succeeds; silent otherwise |
| `DashboardHome` | 4 stat cards, alert panels, quick actions, **Round Directive briefing card**, session status table | alert / no-alert; briefing card hidden if teleprompter fetch fails |
| Floating action bar (fixed bottom) | role badge, selected-session chip, ⚡ Override / 📬 Message / ↩️ Undo, shortcut hints | buttons disabled at 40% opacity when no session selected — no explanation |
| Session-dependent tabs (~12) | Teleprompter, Debrief, Undo, Manual Override, Swipe File, Notes, Bonuses, Peer Eval, Auto-Pause, Interventions, Complexity Feed, Annotations, Materiality | each implements its own "select a session first" empty state (or none) |
| Activity log | in-memory, capped at 50 entries, lost on refresh | populated by WS events + local actions |

---

## 2. Findings — Facilitator screen

### F1 🔴 A dropped WebSocket silently freezes the whole dashboard
**Where:** `admin/facilitator/page.js:525–565` (WS setup), `584–600` (leaderboard fetch).
**What:** The leaderboard is fetched once on mount. Every later refresh depends on WS messages (`sessions_refresh`). The WS has no `onclose` handler, no reconnect, no heartbeat, and there is no polling fallback. If the connection drops mid-workshop (venue Wi-Fi blip, backend restart), every panel keeps rendering the last snapshot indefinitely — rounds, treasuries, alerts all stale — and the only signal is a line buried in the Activity Log. Worse, the `onerror` log says *"using seed data (backend offline)"*, which is false: `SEED_LEADERBOARD` (line 50) is declared but never used anywhere.
**Why it matters:** A facilitator making a pacing or intervention decision from a frozen leaderboard is making it on wrong data with full confidence.
**Fix:** (a) WS auto-reconnect with exponential backoff + a ping/heartbeat; (b) low-frequency polling fallback (e.g. 30s, matching God Mode) that activates while the WS is down; (c) a persistent connection/staleness indicator in the top bar — "● Live · updated 8s ago" / "⚠️ Reconnecting — data may be stale"; (d) correct or delete the seed-data log message.
**Rejected quick fix:** just adding a 30s poll. It papers over the dead socket (events like `pacing_override` and `system_freeze` would still be lost), and the facilitator still gets no visible signal that liveness degraded. The honest indicator is the point.

### F2 🔴 Session selection is fragmented and nearly invisible
**Where:** `_setSelectedSession` (page.js:390–403); `LeaderboardMatrix.js:146–147` (selection = clicking a table row, no checkbox/radio/button affordance); `FacilitatorTeleprompter.js:697–741` (own dropdown); `RoundPacingControl.js` (own local `sessionId`, silently defaults to the **first** session in the list); `DashboardHome` (ignores selection entirely, see F3).
**What:** ~12 tabs consume `selectedSession`, but the only general way to set it is knowing that clicking a Leaderboard row selects it. The quick-action bar (Override / Message / Undo) is disabled until that happens. Meanwhile three different components implement three different selection models, so "which cohort am I acting on?" has three different answers on three tabs.
**Why it matters:** Under time pressure, the dominant facilitator workflow is "something happened in Cohort X → intervene." Today that is: remember the hidden convention → Leaderboard → click row → navigate back → act. Selection mistakes here are how an override lands on the wrong cohort.
**Fix:** One **global cohort selector** in the persistent chrome (top bar or the existing floating action bar, next to the selected-session chip), writing to the same `selectedSession` state everything already reads. All per-tab pickers (Teleprompter, Pacing) become views of it. Leaderboard rows get an explicit "Select" affordance + a visible selected style beyond the subtle row highlight. Every session-dependent empty state embeds the same picker instead of the instruction "go to the Leaderboard."
**Rejected quick fix:** adding "select a session in Leaderboard first" text to more empty states. That documents the friction instead of removing it, and does nothing about `RoundPacingControl` defaulting to the first cohort — which is the actively dangerous variant (acting on cohort A while believing it's cohort B).

### F3 🔴 The Round Directive card can brief the wrong round
**Where:** `DashboardHome.js:48–51` — `currentRound = Math.max(...leaderboard.map(s => s.round_number))` across **all** sessions.
**What:** The prominent "ROUND N DIRECTIVE" briefing card (per your screenshot, the thing a facilitator reads before the round) is keyed to the *maximum* round of any session on the board — including other facilitators' cohorts for super-admins, and player sub-sessions. If your room is on R3 while any other cohort has reached R6, the home card shows the R6 script. The Teleprompter tab does this correctly (derives round from the selected cohort, page.js:758–770); the home card contradicts it.
**Fix:** Key the card to the selected cohort (falling back to the facilitator's only cohort when there's exactly one), and print the cohort name inside the card header ("R3 Directive — Cohort Alpha") so the binding is visible. This is presentation-only; the teleprompter endpoint is untouched.

### F4 🔴 Destructive-action guards are inconsistent, and one is an illusion
**Where:** `handleResetAll` (page.js:656–668): second dialog says *"Are you absolutely sure? Type OK to proceed."* — but it's a native `confirm()`; there is nothing to type. The "guard" is a second OK click wearing a costume. `handleResetSession` (621–654): a chain of 2–3 native confirms. `UndoRound.js:41–50`: two confirms. `FacilitatorSessionManager` (1745–1771): one confirm, then **`window.location.reload()`** on success — mid-session, that dumps the facilitator back to Dashboard Home and wipes the activity log (see F11). Hard-delete visibility is gated on `authData?.facilitator_id === 'admin'` (line 1829) — a magic string, not the role model used everywhere else.
**Why it matters:** Repeated identical confirms train click-through (confirm fatigue), which is exactly how a live cohort gets deleted. Meanwhile the genuinely good pattern already exists in this codebase: God Mode's Factory Reset (typed phrase + 15s countdown + cancel).
**Fix:** One shared confirmation modal component with three tiers: (1) plain confirm for recoverable actions (soft delete), (2) impact-preview confirm showing blast radius ("deletes cohort *Alpha* and **6 player sessions**, currently at R4") for hard deletes and rollbacks, (3) typed-phrase confirm for anything irreversible and plural (reset-all). Replace `window.location.reload()` with the existing `fetchLeaderboard()`. Gate hard-delete on `isSuperAdmin`, not the string `'admin'` (display-layer change; the server check stays authoritative).
**Rejected quick fix:** swapping `confirm()` text so it no longer says "type OK". That fixes the lie but keeps the fatigue pattern and the reload-nuke, i.e. the underlying problem: destructive actions don't communicate scope.

### F5 🟠 Round Timeline labels contradict the actual rounds
**Where:** `RoundTimeline.js:9–20` — hardcoded `ROUND_LABELS` (R1 "Water Crisis", R2 "CFO Gate", R4 "Data Ethics", R5 "Carbon Trading", …).
**What:** The real round themes (per `SIMULATION_CONTEXT.md` / `round_configs.py` and the Teleprompter itself) are R1 ESG Baseline Audit, R2 Double Materiality, R4 Contagion, R5 Physical Climate Risk, etc. The timeline — the facilitator's primary "where is everyone" glance — carries stale labels from an earlier design, directly contradicting the Round Directive card on the same screen.
**Fix:** Delete the hardcoded map; source round titles from the same backend data the teleprompter already fetches (`/api/admin/teleprompter` script titles), with the round number alone as fallback.
**Rejected quick fix:** re-hardcoding the *correct* labels. It repeats the drift mechanism — next content change desyncs it again. The fix is a single source of truth, not fresher duplication.

### F6 🟠 Alert counts are inflated and double-counted
**Where:** `DashboardHome.js:11–42`.
**What:** `lagging` / `lowTreasury` / `lowRep` are computed over **all** sessions — cohort rows *and* their player sub-sessions — so one struggling team can be counted twice (as itself and via its cohort aggregate) and up to three times across categories (`alertCount` is a plain sum of overlapping sets). Treasury alerts are relative to the cross-cohort mean, so a healthy room with one rich cohort flags everyone else. Alert cards are not clickable — no path from "3 Low Treasury" to *which* teams.
**Why it matters:** The Active Alerts card is the facilitator's triage entry point. Inflated counts cause alarm fatigue; the missing drill-down forces a manual leaderboard hunt.
**Fix:** Compute alerts over player sessions within the facilitator's cohorts only; dedupe (a team appears once, with all its flags); use absolute pedagogical thresholds (rep < 40 already is one; treasury < a config floor rather than "50% of mean"); make each alert card navigate to the Leaderboard pre-filtered to those teams.

### F7 🟠 The CEO Interview panel displays global state as per-cohort state
**Where:** `InterviewControlPanel` (page.js:1450–1464): the per-cohort map is seeded by fetching **global** settings and copying `ceo_interview_enabled` onto *every* session row; toggles then PUT per-session.
**What:** The UI renders a per-cohort ON/OFF list whose initial values are not per-cohort — after any per-session change followed by a page reload, the panel shows every cohort with the same (global) value, silently misrepresenting cohorts you configured differently.
**Fix:** Read each session's actual value (the per-session GET counterpart of the PUT that already exists), or, if the backend only stores it globally, present the control as global — the UI must not claim a granularity the data doesn't have. Also: this panel and `QuizControlPanel` live *inside the Round Timeline tab*, where nobody looks for session setup; move them to a "Session setup" grouping or into the cohort edit modal, and fix their hardcoded light-palette styling (bright indigo/amber cards inside the dark theme).

### F8 🟠 Disabled quick actions never say why
**Where:** floating action bar (page.js:1210–1242).
**What:** ⚡ Override / 📬 Message / ↩️ Undo render at 40% opacity with `cursor: not-allowed` when no session is selected (or the tab isn't allowed). No tooltip, no hint. This is the first thing a facilitator reaches for in an incident.
**Fix:** Tooltip/title on the disabled state ("Select a cohort first — click here to choose"), and make the disabled button open the global selector from F2. Distinguish "no session selected" from "your role can't do this" — they currently look identical.

### F9 🟠 Two permission systems disagree about what exists
**Where:** sidebar filtering uses `requiredRole` + `allowed_tabs` (`sidebarConfig.js:165–184`); the quick bar checks only `canAccessTab` (allowed_tabs); `renderActiveComponent` renders any known tab id regardless; `DashboardHome` quick action "📝 Audit Trail" navigates to `audit_trail` — a tab that is **not in the facilitator sidebar at all** (the case survives at page.js:836 "merged into Decision History"), so the breadcrumb falls back to "Command Center › Overview" and no nav item highlights.
**What:** Users can land on screens the nav says don't exist, and (depending on `allowed_tabs`) a base facilitator can reach lead-only tools like Undo Round through the quick bar even though the sidebar hides them — the server will reject the action, but only after the facilitator has invested clicks and trust.
**Fix:** One `canAccess(tabId)` helper (role + allowed_tabs) consumed by sidebar, quick actions, keyboard shortcuts, *and* the tab router; navigation targets must exist in the sidebar config (point the quick action at `decision_replay`, or reinstate `audit_trail` as a real item). Unknown/forbidden tab → visible "not available for your role" state, not a silent fallback.

### F10 🟠 Mutations fail silently
**Where:** pervasive `.catch(() => {})` — scaffolding status, god-visibility, override list; `QuizControlPanel`/`InterviewControlPanel` catch errors to `console.error` only; toggle handlers update UI **only** on `res.ok` — on failure nothing happens at all (no error, no revert cue, button just doesn't change).
**What:** During a live session, "I clicked it and nothing happened" is indistinguishable from "it worked but the UI is slow." Facilitators re-click, double-apply, or move on believing a setting stuck.
**Fix:** A single toast/inline-status pattern for every mutating call: pending → success/failure, with failure naming the action ("Quiz difficulty not saved — retry"). The pattern already half-exists (`status` chips with 3s timeouts in three components); standardise and make the *failure* branch mandatory.

### F11 ⚪ The "Activity Log" is ephemeral but named like an audit trail
**Where:** `activityLog` state (page.js:567–572) — in-memory, 50 entries, wiped by refresh (and by F4's `window.location.reload()`).
**Fix:** Keep it as a live feed but label it "Live feed (this session)"; the durable record is the server-side AuditTrail component — link to it from the log header. No data-flow change.

### F12 ⚪ Small frictions
- **Ctrl+B** hijacks the browser/global bold shortcut; **Ctrl+1–4** closes all other sidebar groups (exclusive-open) — surprising; hints are 0.68rem text in the bottom bar. Consider a `?` shortcut-sheet overlay and non-conflicting bindings.
- God Mode has a mobile sidebar toggle pattern missing (see G7) while facilitator has one; god-mode `sidebarOpen` state (god-mode/page.js:535) is dead code.
- Emoji-as-iconography is charming but inconsistent at a glance (🐢 vs 💸 vs 📉 alert cards); severity should also be encoded by position/colour token, not emoji alone (colour-blind-safe work from the prior review applies here too).

---

## 3. Findings — God Mode screen

### G1 🔴 The header lies when the backend is down
**Where:** `SystemContextBar` (god-mode/page.js:464–530): `const activeCohorts = status ? status.total_cohorts : 0; const isOptimal = status ? (status.system_memory_mb || 0) < 500 : true;`
**What:** When `/god/system-status` fails (backend down, auth expired), the sticky header renders "Live Cohorts: 0 · Active Players: 0 · System Health: 🟢 Optimal". During an outage — the exact moment this bar matters — it actively reassures. Separately, "health" is solely memory < 500MB, which is not a health signal a facilitator can act on.
**Fix:** Tri-state header: **Live** (fresh fetch) / **Stale** (last success > 2 intervals ago, show "as of HH:MM:SS") / **Unreachable** (red, "backend not responding"). Never render fabricated zeros; show the last-known values greyed with a timestamp. Base "health" on observable signals: fetch success, WS connection count, frozen flag.
**Rejected quick fix:** flipping the ternary default to `isOptimal=false` when status is null. That trades a false "Optimal" for a false "Warning" and still shows fake zeros — the underlying issue is that the bar has no concept of data freshness.

### G2 🔴 Platform-wide toggles fire on a single click with no blast-radius signal
**Where:** `GodModeStatus.js:193–294` — ~29 pills (12 Pedagogical Scaffolding + 17 System Engine Modules), each an immediate PATCH to `global-settings` on click. Feedback is a 3-second status line rendered *above the whole section*, physically far from the clicked pill. No confirmation for anything — including toggles that visibly change live player experience mid-round (Decision Timer, Market Sim, Front Page, R6 Twist).
**What:** These are the most consequential controls on the platform, rendered as the smallest targets (0.68rem, 3×9px padding), one accidental click from mutating every live cohort. Facilitators only learn about it via a log line ("⚙️ God Mode updated: …").
**Fix:** (a) For live-impacting toggles, an inline confirm popover with blast radius: "Enable Decision Timer — affects **3 live cohorts (42 players) currently mid-round**. Apply?" (cohort count is already client-side via the leaderboard; no new backend). (b) Per-pill state feedback: pending spinner → ✓/✗ on the pill itself, replacing the distant status line. (c) Visual tier separation: session-content toggles (R6 Twist, Tribunal) vs engine modules vs metacognitive aids — currently one undifferentiated pill soup. (d) Optionally a "batch" mode: stage several pills, one Apply.
**Rejected quick fix:** wrapping every pill in `confirm()`. Twenty-nine native dialogs is fatigue-by-design (see F4), and `confirm()` can't show the affected-cohort count, which is the actual decision-relevant information.

### G3 🟠 Emergency Freeze: cramped input, asymmetric guard
**Where:** `GodModeStatus.js:46–58, 134–173`.
**What:** The freeze message lives in a 180px input (your screenshot shows "System maintenance in prog" truncated — what players will see, invisible to the admin). Freeze requires a native confirm; **Unfreeze requires none** — a stray click resumes all paused simulations, which mid-incident may be the more dangerous direction. Frozen state is visible only inside the GodModeStatus card; navigate to any other tab and nothing on screen says the platform is frozen (facilitators get a strip chip; God Mode itself doesn't).
**Fix:** Freeze panel with a full-width message field + live preview of the player-facing banner; symmetric confirms both directions ("Unfreeze — 3 cohorts resume immediately"); a persistent "❄️ SYSTEM FROZEN" ribbon in the God Mode chrome (SystemContextBar is already sticky and knows `system_frozen` — render it there) so the state survives tab changes.

### G4 🟠 Three overlapping "system status" surfaces, none authoritative
**Where:** `SystemContextBar` (15s poll) + `GodModeStatus` cards (10s poll) + `SessionHealthDashboard` (15s poll) all on the default tab; leaderboard on a 4th 30s poll.
**What:** The same counts render twice within one viewport (your screenshot: "Live Cohorts: 9" in the bar, "9 COHORTS" in the card grid), refreshed on different clocks — so they can disagree for up to ~15s, which reads as a bug and erodes trust in all of them. Four timers also quadruple the failure modes G1 describes.
**Fix:** One client-side status store (context/provider) with a single poll interval feeding bar, cards, and health monitor. The bar becomes a compact echo of the same data, so they can never disagree. Pure client refactor; endpoints and payloads unchanged.

### G5 🟠 Per-tab session targeting is inconsistent
**Where:** god-mode/page.js — `debrief_view` and `regulatory_sandbox` render their own cohort dropdowns; `materiality_config`, `decision_timeline`, `dna_comparison` receive `selectedSession` with no picker on the tab; the dropdowns disappear entirely (rather than showing a disabled/empty state) when no cohorts exist; selection made in Platform Analytics (`onSelectSession`) invisibly changes what Materiality Config will target later.
**Fix:** Same remedy as F2 — a single global cohort selector in the God Mode chrome, with each tab displaying "Target: <cohort>" and offering the picker inline when unset. Selection becomes visible state instead of hidden coupling between tabs.

### G6 🟠 "No cohorts active" can mean "your request failed"
**Where:** `DangerZonePanel` (god-mode/page.js:972–980): fetches `/api/admin/sessions` **without** `credentials: 'include'` (most other god-mode calls include it), and on error just `setLoading(false)` — rendering the same "No cohorts active" empty state as a genuinely empty database. Several other god-mode GETs (`system-status`, `god/settings`, `session-health`) also omit credentials.
**What:** In the one screen dedicated to mass deletion, an auth/network failure is indistinguishable from "there is nothing here" — and an admin who believes the DB is already empty behaves differently around a Factory Reset button.
**Fix:** A shared authed-fetch helper (single place for `credentials: 'include'` + error normalisation), and empty-vs-error differentiation in every table: "No cohorts" vs "Couldn't load cohorts — retry". This is a hygiene fix but it must ride with any Danger Zone work.

### G7 🟠 Sidebar/router drift and overpromising tooltips
**Where:** god-mode/page.js + sidebarConfig.js.
- `case 'cohort_orchestration'` (page.js:641) is unreachable — no sidebar item has that id.
- **Session Controls** tooltip promises "Round pacing, universal broadcasts, visibility controls, and cross-cohort scheduling" but the tab renders only `UniversalBroadcast` (page.js:648–653). An admin hunting for pacing controls is sent to the wrong tab by the UI's own documentation.
- `sidebarOpen` state is dead; no mobile toggle (facilitator has one) — relevant if you ever drive God Mode from a tablet at the podium.
- Ctrl+B targets `session_controls` here but `broadcast` on the facilitator screen — same shortcut, different semantics.
**Fix:** Reconcile config with router (delete dead cases or add the item); rewrite tooltips to describe what tabs actually contain (or move `RoundPacingControl` into Session Controls, where the tooltip — and users — expect it); align the shortcut semantics.

### G8 ⚪ Auth-header inconsistency
`GodModeStatus` PATCHes still send `X-Facilitator-Id` (lines 213, 277) while the rest of the app migrated to the JWT cookie (the M2 comment in god-mode/page.js documents the migration). If the backend ever drops header support, these toggles fail — and per F10-style silent-failure handling, they'd fail invisibly. Align on the cookie path.

### G9 ⚪ Tone and polish
- "☢️ Factory **Nuke** All Sessions" — the type-to-confirm + countdown mechanics are excellent (adopt platform-wide per F4); the copy will read badly the day a client admin sees it.
- Trading Floor / Shockwave external links are styled as ordinary nav items; Shockwave (mass crisis detonation) merits its console's danger framing at the entry point too — at minimum the tooltip should say it opens a *destructive* console.
- Heartbeat-emoji animation in the context bar: fun, but it implies liveness even when data is stale (see G1) — tie the animation to actual fetch success.

---

## 4. Phased implementation plan

Design principles: **(1)** every phase touches only `frontend/app/admin/*` and admin-only components — never `hooks/useSimulation.js`, the player `page.js`, or player-cockpit components; **(2)** phases are ordered so that read-only rendering changes land before anything that wraps a mutation; **(3)** no phase changes *which* HTTP requests are sent, their payloads, or their timing on the player side.

**⚠️ Shared-component register (touch with dual-surface testing only):** `DebriefReport`, `MaterialityConfig`, `RegulatorySandboxControl`, `TechnicalGlossary`, `BalancedScorecardEvaluator`, `ComplexityEventFeed`, `DecisionTimeline`, `DNAComparison`, `PlatformAnalytics` are rendered by *both* dashboards; `FacilitatorTeleprompter` imports `BRIEFINGS` from the **player-side** `RoundBriefing.js`. Any edit to these requires checking both admin screens; any edit to `RoundBriefing.js` is out of scope entirely (player-facing).

---

### Phase 0 — Safety net (no UI changes)
**Do:** Branch per phase (`ux/phase-1`, …). Record a baseline: (a) screenshots of every tab on both screens; (b) a network-contract snapshot — with dev tools open, walk both dashboards and export the HAR; the set of endpoints + methods + payloads is the regression oracle for "data flow unchanged"; (c) scripted participant smoke test (Puppeteer is already in the repo): player joins cohort → makes R1 crisis + pillar decisions → round advances → dashboard KPIs render. (d) Run the backend test suite once for a green baseline (no backend files will be edited in any phase, but the suite guards against accidental cross-boundary edits).
**Rollback:** n/a.

### Phase 1 — Read-only truth (lowest risk: display logic only)
**Scope:** F3 (briefing card keyed to selected cohort + cohort name in header) · F5 (round labels from teleprompter data) · F6 (alert math + clickable alert cards) · F11 (log renamed/linked) · G1 (tri-state context bar + last-updated) · G4 (single status store) · G7 (sidebar/router reconciliation, tooltip copy) · F1(d) (delete the false seed-data message).
**Why first:** No mutations touched, no new endpoints, no state written — pure rendering and client-side derivation. Highest facilitator payoff per unit of risk.
**Testing checklist:**
- [ ] HAR diff vs Phase 0: identical endpoint set (G4 may *reduce* duplicate calls — verify no *new* ones, and that the surviving poll interval ≥ the old shortest interval so backend load doesn't rise).
- [ ] With two cohorts at different rounds, home briefing card matches the *selected* cohort's round and equals the Teleprompter tab's round.
- [ ] Round Timeline labels equal Teleprompter script titles for R1–R10; kill the teleprompter endpoint → timeline still renders "R1…R10" (fallback path).
- [ ] Alert counts: hand-count one seeded scenario (e.g. 1 team low-rep *and* low-treasury → appears once, alertCount correct).
- [ ] Stop the backend → context bar shows Unreachable within 2 intervals; restart → recovers to Live; at no point shows "0 · Optimal".
- [ ] Participant watch: run the Phase 0 player smoke — zero changes expected (no player files in the diff; verify with `git diff --stat` path whitelist).
**Rollback:** `git revert` the phase merge commit. No persisted state, no schema, no localStorage format changes — revert is complete by itself.

### Phase 2 — Feedback & error surfacing (low risk: additive UI around existing calls)
**Scope:** F10 (standard pending/success/failure status on every mutating call in both dashboards) · F8 (disabled-reason tooltips on quick actions) · G6 (authed-fetch helper + empty-vs-error states) · G8 (cookie-auth alignment for the two PATCH sites) · scaffolding-strip "last synced" chip.
**Boundary discipline:** The fetch helper must not alter payloads or add headers beyond `credentials: 'include'` (which the backend already accepts everywhere per the M2 migration). G8 removes a header the backend documents as ignored for auth — confirm against `admin_router.py` before removing, else keep sending both.
**Testing checklist:**
- [ ] For each mutating control (quiz difficulty, quiz toggle, interview toggle, scaffolding pill, engine pill, override, freeze): success path shows confirmation *at the control*; then repeat with backend stopped → visible failure message, UI state does **not** optimistically flip.
- [ ] HAR diff: same endpoints, same bodies; only the `credentials` flag / removed header differ where specified.
- [ ] 401 simulation (delete cookie): Danger Zone shows "couldn't load" state, not "No cohorts active".
- [ ] Participant watch: none of these components are player-rendered; run player smoke anyway (settings toggles exercised during the test must produce identical player-side behavior — toggle Front Page off/on and confirm the player reveal honors it exactly as before).
**Rollback:** revert the phase commit. The fetch helper is additive; reverting restores the old inline fetches verbatim.

### Phase 3 — Unified session selection (medium risk: state plumbing, no new writes)
**Scope:** F2 + G5 — global cohort selector component in both chromes; Teleprompter/Pacing/Debrief/Sandbox pickers become controlled views of `selectedSession`; leaderboard row selection gets explicit affordance; session-dependent empty states embed the picker; **remove `RoundPacingControl`'s default-to-first-session behaviour** (unset = explicit "choose a cohort" state).
**Risk & isolation:** This changes *which sessionId* flows into components — the one place a UI bug could target the wrong cohort. Mitigate: the selector writes to the *existing* `selectedSession` state (same persistence key `fac_selected_session`), so all current consumers are untouched; per-tab pickers are converted one at a time, each its own commit.
**Testing checklist (per converted picker, before moving to the next):**
- [ ] Select cohort A in the global selector → open the tab → its requests carry cohort A's session_id (network tab check against Phase 0 HAR patterns).
- [ ] Switch to cohort B mid-tab → in-flight data clears/reloads for B; no A-data rendered under B's name.
- [ ] Pacing tab with nothing selected shows "choose a cohort", performs **no** pacing GET/PUT (this is the behaviour change — verify no request fires, vs. old auto-first-session GET).
- [ ] Refresh browser → selection persists (localStorage) and every tab agrees.
- [ ] Cross-screen: God Mode selection does not leak into Facilitator selection (separate keys) unless you decide otherwise.
- [ ] Participant watch: pacing is the sensitive surface here — with a live player connected, change pacing mode for cohort A and confirm **only** cohort A's player receives `pacing_override`; player round-unlock timing unchanged (compare `next_unlock_at` before/after a no-op mode re-save).
**Rollback:** revert the phase merge; because the persistence key and consumer state are unchanged, reverting cannot strand state. If only one converted picker regresses, revert that picker's commit alone.

### Phase 4 — Live-data resilience (medium-high risk: touches the admin WS lifecycle)
**Scope:** F1 — admin-WS reconnect with backoff + heartbeat, polling fallback while disconnected, persistent Live/Stale/Reconnecting indicator in the facilitator chrome (reusing G1's freshness model).
**Risk & isolation:** Only the **admin** socket (`/api/admin/ws/admin`) is touched. The player socket lives in `useSimulation.js` and is explicitly out of scope. Reconnect must be idempotent (close old socket before opening new; cap backoff; stop on logout). Polling fallback reuses the existing `fetchLeaderboard` — no new endpoint.
**Testing checklist:**
- [ ] Kill backend 30s, restart → indicator: Live → Reconnecting → Live; leaderboard resumes updating; exactly one WS connection open afterwards (check server-side `active_ws_connections` in God Mode — no connection leak from repeated reconnects).
- [ ] While disconnected: polling fallback updates leaderboard on schedule; indicator shows Stale/Reconnecting, never Live.
- [ ] Broadcast + pacing_override during a disconnect window → after reconnect the *next* events flow; document (in the indicator tooltip) that events during the gap appear in the server AuditTrail, not the live feed.
- [ ] Laptop-sleep/wake (the real-world trigger): wake → reconnect within backoff cap without manual refresh.
- [ ] Participant watch: with a player mid-round, bounce the *admin* connection repeatedly → player WS uninterrupted (player screen never reconnects, no round-state flicker, decisions submit normally). This is the single most important test in the phase.
**Rollback:** revert restores the old connect-once socket. No server change, no protocol change — old and new clients are wire-identical.

### Phase 5 — Destructive-action & global-toggle hardening (highest risk: wraps mutation triggers)
**Scope:** F4 (shared 3-tier confirm modal; replace all `confirm()` chains; impact previews; remove `window.location.reload()`; role-gate hard delete on `isSuperAdmin`) · G2 (blast-radius popovers + per-pill status on global toggles; toggle grouping) · G3 (freeze panel: full message field + preview, symmetric confirms, persistent frozen ribbon) · F9 (single `canAccess` for sidebar/quick-bar/router; fix `audit_trail` quick action).
**Risk & isolation:** The invariant: **request payloads and endpoints are byte-identical to Phase 0** — only the gate *in front of* each request changes. The blast-radius counts are computed client-side from the leaderboard (no new endpoints). Server-side authorization remains the real enforcement; frontend gating changes are display-layer.
**Testing checklist:**
- [ ] For every wrapped action (soft delete, hard delete, cohort rollback, reset-all, freeze, unfreeze, each live-impacting toggle): confirm-then-execute produces a request identical (method, URL, body) to the Phase 0 HAR; cancel produces **no** request.
- [ ] Typed-phrase modal: wrong phrase keeps execute disabled; countdown cancel truly aborts (no request fired) — mirror the existing Factory Reset tests.
- [ ] Impact preview numbers: create a cohort with a known player count → preview says exactly that; delete → server response `players_removed` matches the preview.
- [ ] Post-delete: leaderboard refreshes in place (no full reload); selectedSession referencing a deleted cohort clears gracefully everywhere (quick bar, tabs, selector).
- [ ] Role matrix: log in as facilitator / lead / super_admin → sidebar, quick bar, and direct-navigation all agree per role; server still rejects any bypass attempt (negative test with hand-crafted state).
- [ ] Participant watch: (a) toggle a live-impacting setting through the new popover → player-side effect identical in content *and timing* to Phase 0 (e.g., Decision Timer appears on player screens at the same tick); (b) freeze → player maintenance banner shows the **full** untruncated message; unfreeze → players resume, round state intact; (c) rollback a test cohort → players receive the same rollback notification as before, land on the same round with the same KPIs (compare a `/dashboard` payload before/after against a Phase 0 rollback capture).
**Rollback:** each control family (deletes / freeze / toggles / gating) is its own commit — revert selectively. Because payloads are unchanged, reverting a gate cannot leave the backend in an inconsistent state; the worst case of a bad revert is the old confirm chain reappearing.

### Phase 6 — Structural polish (optional, cosmetic)
**Scope:** F7 panel relocation + per-cohort read (needs a small backend GET *only if* the per-session value isn't already readable — if it isn't, defer this item rather than touch the backend, per constraints) · F12/G9 (shortcut sheet, non-conflicting bindings, copy pass on "Nuke", Shockwave entry framing, theme-token pass on Quiz/Interview panels, dead-state cleanup: `sidebarOpen`, `cohort_orchestration`, `SEED_LEADERBOARD`).
**Testing checklist:** visual regression against Phase 5 screenshots; keyboard shortcut audit on Windows + macOS; player smoke unchanged.
**Rollback:** revert; all items independent.

---

## 5. Standing test protocol (run at the end of every phase)

1. `git diff --stat <phase-base>` — confirm the path whitelist: no `backend/`, no `hooks/useSimulation.js`, no player-side components, no shared-register component without its dual-surface check.
2. Backend `pytest` — must remain at the Phase 0 green count (it will, since no backend edits are in scope; this catches accidents).
3. Player E2E smoke (Phase 0 script): join → R1 crisis + pillars → advance → KPIs. Must pass unmodified — the script itself is never edited to accommodate a UI change; if it fails, the phase regressed the participant flow and gets reverted, not the test.
4. HAR contract diff for both admin screens: endpoint set, methods, payloads. Additions/removals must be explicitly listed in the phase's notes (only Phases 1 and 4 legitimately change call *frequency*; none change payloads).
5. One live two-browser rehearsal: facilitator screen + player screen side by side through two rounds, exercising the phase's new surfaces, watching the player screen for *any* unprompted change (re-render, reconnect, timing shift).

---

## 6. Priority order (if you do nothing else)

1. **Phase 1's G1 + F3 + F5** — these three make the dashboards *stop misinforming* the facilitator, for pure display-logic cost.
2. **Phase 4 (F1)** — the silent-freeze failure mode is the one that ruins a session and gets misdiagnosed as "the sim broke."
3. **Phase 3 (F2)** — unified selection is the largest per-click time saving during live incidents.
4. **Phase 5 (F4 + G2)** — guards that inform instead of nag; do this before the next session where a non-owner admin has God Mode access.

---

*All file/line references are against the current working tree (checked 2026-07-05). Happy to turn any phase into a concrete change list per file, or draft the ConfirmModal / status-store / selector component specs next.*
