# Muressons — UI/UX Review v3: God Mode & Facilitator (New Surfaces Since v2)

*Third systematic pass, run against the current tree (2026-07-11, HEAD `141a331`).
Process per the brief: code read first, then hierarchy/state mapping, then friction
points with concrete fixes. Review and plan only — no code changed. Hard constraints
unchanged: simulation logic, scoring, and data flow stay functionally identical; the
participant experience must not change or be put at risk; no symptom-patching quick
fixes without flagging them.*

**Severity key:** 🔴 blocks facilitator · 🟠 slows facilitator · ⚪ cosmetic

---

## 0. Prior context and what this pass covers

**Status of v1 + v2 findings — verified intact in the current tree.** All 21 v1
findings (F1–F12, G1–G9, commits `559f8d2`…`d422693`) and all 8 v2 findings
(V2-1…V2-8, Phases R1–R5, commits `e48406d`…`c0355f2`) are implemented and
survive today: spot-checked the tri-state header, single status poller,
`CohortSelector`/`requireCohort` empty states, WS liveness chip
(facilitator/page.js:1467), tiered `ConfirmModal`, leaderboard sort/search,
teleprompter presentation mode (R4 block at FacilitatorTeleprompter.js:600),
cohort-setup checklist with per-item retry (CreateCohortModal.js:513–723), and
the `flexWrap` bar fix (page.js:1432). No regressions found in the audited fixes.

**What changed since v2 and was never audited** — this is where v3 goes:

- **W-B/W-C/W-D/W-E "WOW" features:** Trading-Floor finale additions (rival NPC row,
  staggered reveal, IPO delta), the new **Region War-Map** projector
  (`admin/war-map/page.js`), and the **Situation-Room voice bulletin** in the
  Teleprompter.
- **Console links moved from God Mode to the facilitator sidebar** (page.js:1336–1400),
  gated by new per-facilitator capability flags (`trading_floor_enabled`,
  `shockwave_enabled`, `situation_room_enabled`).
- **`project_admin` role** (registry + cohort provisioning only; backend
  `admin_shared.py:60` fixed tab set) with **Excel bulk upload** in
  `FacilitatorManager`.
- **Master-password rotation modal** in God Mode (god-mode/page.js:287–402) and the
  password-visibility/`PasswordInput` pass.
- The **Shockwave console** (`admin/shockwave/page.js`) — present before v2 but
  never audited (v1 touched only its sidebar entry framing).

Files read for this pass: `admin/war-map/page.js` (217 ln), `admin/shockwave/page.js`
(118 ln), `admin/trading-floor/page.js` (274 ln), `admin/god-mode/page.js` (1,514 ln),
`admin/facilitator/page.js` (2,196 ln), `FacilitatorTeleprompter.js` (1,884 ln),
`FacilitatorManager.js` (2,544 ln), `CreateCohortModal.js`, `DashboardHome.js`,
`sidebarConfig.js`, `warMapModel.js`, plus backend cross-checks (read-only, to verify
UI truthfulness): `admin_shared.py` (roles/tabs), `admin_router.py`
(`_SHOCKWAVE_EVENTS` 4184–4189, `detonate_shockwave` 4208+, `finale_ring_bell`
7118–7134, bulletin endpoint), and player-side `app/page.js:755–785` (WS message
handling — read as evidence only; player files stay untouched).

---

## 1. Screen maps — deltas since v2

### 1.1 Facilitator screen (incl. its satellite consoles)

| Surface | Contents | States observed in code |
|---|---|---|
| Sidebar (new) | `Administration` group (registry, shown when `allowed_tabs` grants it); 3 external console links at the bottom: Trading Floor 🔔 / Shockwave 🌊 / War-Map 🗺️, capability-gated except War-Map | links open new tabs; hidden when flag false |
| Teleprompter (new) | `🎙️ Market Bulletin` button in the presentation-controls row; chyron overlay with live dot, dismiss, reduced-motion support | idle / busy ("Synthesizing…") / error (named, `role="alert"`) / chyron / audio-autoplay-refused fallback — **well built** |
| Trading Floor `/admin/trading-floor` | own ON/OFF (localStorage), 5s leaderboard poll, ticker, ranked board + NPC benchmark row, **Ring the Closing Bell** → `market_close` broadcast + staggered reveal + confetti | off / error ("Waiting for the backend / facilitator sign-in…") / empty / live / closed |
| War-Map `/admin/war-map` | own ON/OFF (localStorage), 5s leaderboard poll, SVG map, crisis pulses, R5 cyclone, event ticker | off / error (same conflated message) / live; `prefers-reduced-motion` respected |
| Shockwave `/admin/shockwave` | cohort dropdown (auto-selects first), 4 hardcoded crisis cards, countdown input, two-step inline Detonate confirm | error banner / result banner / confirming |
| Registry (facilitator portal) | same `FacilitatorManager` God Mode uses; CSV path = parse → preview → submit; **.xlsx path = immediate server-side creation** | drag-over / uploading / per-row errors / toast |
| Dashboard Home (project_admin) | full facilitator dashboard: alert cards, quick actions, briefing card, session table | unchanged from lead/facilitator view |

### 1.2 God Mode

| Surface | Contents | States observed in code |
|---|---|---|
| Header (new) | account chip + **two adjacent icon-only buttons**: 🔑 (own password) and 🗝️ (MASTER password), then Logout (god-mode/page.js:1022–1055) | tooltips only distinguish them |
| MasterPasswordModal | current-pw + new + confirm, min-8 check, named errors, success screen | idle / loading / error / success |
| Sidebar | console links **removed** (moved to facilitator portal); no replacement entry point | — |
| Router | `case 'glossary_editor'` (page.js:916) has **no sidebar item** → unreachable dead case | — |

---

## 2. Findings — Facilitator screen

### F-1 🔴 Shockwave console auto-targets the first cohort and confirms blind
**Where:** `admin/shockwave/page.js:38` (`if (list[0]) setCohort(list[0].id)`);
confirm at 94–98 ("Hit every team in this cohort? Yes — DETONATE").
**What:** This is the exact defect class v1's F2 removed from `RoundPacingControl`
("the actively dangerous variant: acting on cohort A while believing it's cohort B") —
reintroduced on the single most destructive facilitator control. The console ignores
the unified `fac_selected_session` selection entirely (verified: no reference), the
dropdown silently pre-picks whichever cohort the leaderboard returns first, and the
confirm names neither the cohort nor the team count. The blast radius is knowable
client-side (player sub-sessions per cohort are in the leaderboard payload the page
already fetched) and shown nowhere. Impact lands on real treasuries and reputations.
**Fix:** (a) no auto-selection — unset state renders "choose a target cohort", same
convention as every session-scoped tab (`requireCohort` pattern); (b) prefill from
`localStorage['fac_selected_session']` **as a visible default, never a silent one**
("Target: Cohort Alpha — from your dashboard selection · change"); (c) confirm becomes
the platform's tier-2 impact-preview pattern: "Detonate **Global Pandemic** on
**Cohort Alpha — 6 teams, currently R4** (−$6.0M · −6 rep each)?" — all data already
client-side; payload byte-identical.
**Rejected quick fix:** just removing the auto-select. Necessary but not sufficient —
the blind confirm is the half that deletes trust when the wrong cohort gets hit anyway.

### F-2 🔴 Rehearsal mode exists on the server but is unreachable from any UI
**Where:** backend `admin_router.py` `detonate_shockwave` — documented body flag
`rehearsal: true` ("preview on the facilitator's screen only — NO game state changes,
NO student broadcast", WOW-4E) and an admin-WS `shockwave_rehearsal` message. Verified:
zero references to `rehearsal` anywhere in `frontend/` — the console never sends it and
no client handles the WS message.
**What:** The safety feature purpose-built for this console — try the crisis without
touching students — is fully dark. A facilitator's only way to see what a shockwave
looks like is to fire a live one.
**Fix:** A secondary "🎭 Rehearse (no student impact)" button beside Detonate, sending
the **existing** documented body flag to the **existing** endpoint, rendering the
preview card from the POST response (`{status:'rehearsal', event, …}`) directly —
no WS handling required, no new endpoint, no state change (the server guarantees it).
**Constraint note:** this adds one request *variant* the UI never sent before, but the
contract is already defined and enforced server-side as a no-op on game state; it is
called out explicitly in Phase S4's test plan rather than smuggled in.

### F-3 🔴 Ring the Bell: one unconfirmed click, an arbitrary cohort id, and a lie on failure
**Where:** `admin/trading-floor/page.js:83–101` — `ringBell` picks
`teams.find(t => t.parent_cohort_id)?.parent_cohort_id || 'cohort'` (first match, or the
literal string `'cohort'`), fires the POST with `.catch(() => { /* still close the local
view even if broadcast fails */ })`, then closes the board and plays the bell
unconditionally. The button (line 210) has no confirmation of any kind.
**What, in facilitator terms:** (1) One misclick during a live session prematurely
fires the finale — and the player-side handler (`app/page.js:765–767`) shows the
"🔔 Market Closed" overlay to **every connected player in every cohort**, because the
backend broadcasts to all students and the player client doesn't filter by `cohort_id`
(verified both sides; that data flow is out of scope and stays — but the UI must tell
the truth about it). (2) If the POST fails, the projector confidently displays "MARKET
CLOSED — the numbers are final" while no player ever received the overlay: the
facilitator announces a moment that didn't happen. (3) Recovery is undiscoverable —
the only way to un-close is flipping the ON/OFF switch, which nothing communicates.
**Fix:** (a) tier-2 confirm with the honest blast radius: "Ring the closing bell —
freezes this board and shows the Market Closed overlay on **every connected player
screen (all cohorts)**. This is the finale."; (b) surface the POST result: on failure
keep the board live and show "Bell not broadcast — players did NOT see the close.
Retry."; success → proceed exactly as today (identical payload); (c) an explicit
"↺ Reopen board" affordance in the closed state (pure local state, `setClosed(false)`,
which the switch already proves is safe).
**Rejected quick fix:** wrapping the button in `confirm()`. It can't carry the
all-cohorts blast radius — which is the one fact the facilitator must see — and it
does nothing about the swallowed failure.

### F-4 🟠 The same drop zone silently behaves two different ways: CSV previews, Excel executes
**Where:** `FacilitatorManager.js:587–609` (`handleExcelUpload` — POSTs the file,
accounts are created immediately), 613–614 (`handleFileSelect` branches on `.xlsx`),
vs. the CSV path (parse → editable preview table → explicit "create" submit).
**What:** Dropping `facilitators.xlsx` onto the bulk-upload zone creates real accounts
(with live credentials) the moment the file lands — no preview, no confirm — while the
visually identical CSV flow shows a review step first. A project_admin who learned the
CSV flow will drop an Excel file expecting a preview and get 40 created accounts and a
toast. Errors arrive per-row *after the fact*.
**Fix:** Make the commit point explicit and consistent: on `.xlsx` selection show a
pre-flight confirm ("Excel files are parsed on the server — **this creates the accounts
immediately**. N rows can't be previewed client-side. Continue / Cancel"), and render
the response as the platform's existing checklist pattern (created ✓ / skipped ✗ with
row reasons — `bulkErrors` already carries this, it just needs the same visual weight
as the CSV preview). Endpoint and payload untouched.
**Rejected quick fix:** a warning line of copy above the drop zone. Nobody re-reads
copy on a control they've used before; the inconsistent commit point is the defect.
**Proper long-term option (flagged, needs one backend param):** a `dry_run` flag on
`/facilitators/bulk-upload` would allow true Excel preview parity — out of scope under
the no-backend-edit constraint; noted for a future backend cycle.

### F-5 🟠 The project_admin portal is a facilitator dashboard with dead doors
**Where:** backend `admin_shared.py:60` (`project_admin → ['dashboard_home',
'facilitator_registry']`); `DashboardHome.js:190–213` (quick actions hardcode
navigation to `leaderboard`, `registry`, `decision_replay`, `reports`); alert cards
navigate to `leaderboard` (134–184).
**What:** A project_admin lands on the full facilitator Dashboard Home: KPI alert
cards, a round-directive briefing card, a session status table, and five quick actions
— of which **four navigate to tabs their role can't access**, landing on the 🔒 "This
view isn't available" panel (the v1 F9 guard works, so nothing breaks — but the home
screen for this role is mostly invitations to dead ends, with the two things they can
actually do, provisioning and the registry, given no more prominence than the noise).
**Fix:** Pass the existing `canAccessTab` predicate into `DashboardHome` and filter
quick actions and alert-card navigation by it (display-only). For project_admin
specifically, suppress the briefing card and alert section (facilitation artifacts) and
lead with the two real actions: 🚀 Create New Cohort · 👥 Facilitator Registry.
**Also (sidebar hygiene):** `sidebarConfig.js` `ROLE_HIERARCHY` (169–174) doesn't know
`project_admin` (falls through to level 0). Today that's accidentally correct — their
two tabs carry no `requiredRole` — but the first `requiredRole`-tagged tab ever added
to their `allowed_tabs` will silently vanish. Add the role explicitly, mirroring
`admin_shared.py:38`, per the file's own SYNC-WARNING.

### F-6 🟠 Two entry points to cohort creation present the same person with two different modals
**Where:** `CreateCohortModal.js:69–71` — `isBaseFacilitator = role === 'facilitator'
|| (!isSuperAdmin && !isLeadFacilitator)` means **project_admin falls into the
base-facilitator bucket** (locked to self, `canAssignAllTracks` false). But
`FacilitatorManager.js:2530–2532` opens the same modal with
`currentFacilitatorRole="super_admin"` **hardcoded**.
**What:** From Dashboard Home's "Create New Cohort", a project_admin gets the most
restricted modal variant (can't assign the cohort to a facilitator — the core of their
job). From the Registry's per-facilitator "create cohort" button, the identical person
gets the full super-admin variant. Same user, same task, two capability stories; and
the hardcoded `"super_admin"` makes the UI *claim* powers the server may or may not
honor for other roles that reach that path.
**Fix:** One role resolution: the modal receives the caller's true role from
`authContext` at both call sites, and gains an explicit `project_admin` branch whose
capabilities mirror what the backend actually permits the role (facilitator
assignment: yes — that's provisioning; global side-track powers: whatever the server
enforces today, verified against `admin_router.py` before writing the branch, so the
UI never promises above the server). Display layer only; creation payloads unchanged.
**Rejected quick fix:** hardcoding `"project_admin"` at the Dashboard-Home call site
the way the registry hardcodes `"super_admin"`. That doubles the pattern that caused
the bug; the role must come from auth state in both places.

### F-7 🟠 "Create New Cohort" is gated on the role string, not the actual permission
**Where:** facilitator/page.js:846 — `onCreateCohort={authData.role === 'facilitator'
? null : …}`; but the real permission is the per-facilitator `can_create_cohorts`
flag (backend `admin_router.py:1338`, toggled per profile in the Registry UI).
**What:** A lead facilitator whose `can_create_cohorts` was switched off still sees the
button, invests in the 2,265-line modal flow, and gets rejected by the server at
submit. The same mismatch class as v1's F9 (two permission systems disagreeing).
**Fix (flagged as needs-one-backend-field):** the `/me`-style auth payload the page
already destructures (page.js:100) doesn't carry `can_create_cohorts`, so the display
layer *cannot* know. Either add that one read-only field to the auth response (additive,
no behavior change — but it is a backend edit, so it rides only with your explicit
sign-off in Phase S5) or defer. **Interim honest mitigation (pure UI):** keep the
button but let the modal surface the server's rejection as a named, pre-submit check —
the modal's checklist pattern (R3) already knows how to render a failed step.

### F-8 ⚪ The Administration sidebar group is invisible to keyboard shortcuts and the shortcut sheet
**Where:** facilitator/page.js:498 — `categoryKeys = ['command','classroom',
'analytics','config']` (hardcoded); `FACILITATOR_SHORTCUTS` (56–61) says "Ctrl+1…4 ·
Toggle sidebar group".
**What:** With the new Administration group a super_admin has five groups; Ctrl+1–4
addresses the old four, and for a project_admin (two visible groups) Ctrl+1 toggles a
group they don't have. V2-8's single-source-of-truth fix stopped one step short: the
keys are derived from a hardcoded list, not from `FILTERED_SIDEBAR`.
**Fix:** derive `categoryKeys` from the rendered `FILTERED_SIDEBAR` group ids, and
generate the shortcut-sheet line from the same array ("Ctrl+1…N").

### F-9 ⚪ Console chrome truth: toggle scope and error states
**Where:** war-map/page.js:97 + trading-floor/page.js:131 (`title="Facilitator
on/off"`); both error states read "Waiting for the backend / facilitator sign-in…"
(war-map:113, trading-floor:147); war-map header derives "ROUND N" from the global max
round (line 95).
**What:** (1) The ON/OFF switch controls only *this browser tab's* polling, but its
label reads like a platform control — a facilitator at the podium may flip it believing
it hides the projector for players. (2) The error message conflates "backend down"
with "your session expired," which have opposite remedies mid-class. (3) A projector
labeled "LIVE · ROUND 6" while *your* room is on R3 is the F3 defect class in
cosmetic form.
**Fix:** label the switch "Project on this screen: ON/OFF"; split the error copy on
`response.status` (401/403 → "sign in on the facilitator dashboard, then reload this
tab" vs network → "backend unreachable — retrying"); war-map subtitle "ROUNDS 1–6 IN
PLAY" (range, not max) when cohorts diverge.

### F-10 ✅ (no action) The Situation-Room bulletin is the pattern to copy
`FacilitatorTeleprompter.js:609–666, 869–956`: capability-gated button with a
select-a-cohort-first disabled reason, busy state, named inline error (`role="alert"`),
autoplay-refused fallback, reduced-motion support, cleanup on unmount. Noted so the
Phase-S work uses it as the reference implementation for console feedback.

---

## 3. Findings — God Mode screen

### G-1 🟠 Two identical-weight key buttons, one of which rotates the break-glass credential
**Where:** god-mode/page.js:1022–1055 — 🔑 ("Change password") and 🗝️ ("Change the
MASTER password…") rendered side by side, both icon-only, ~24px apart, distinguishable
only by tooltip and a subtle border tint.
**What:** The master password signs in `god_mode` and bypass-logs into **every
facilitator account**. Its entry point is a near-twin of the routine self-serve
password button. The modal itself guards well (requires the current master password),
so a misclick costs confusion rather than catastrophe — but mid-session, an admin
reaching for "change my password" and landing in a red break-glass dialog is exactly
the kind of alarm the chrome shouldn't generate.
**Fix:** text labels ("🔑 My password" / "🗝️ Master key"), physical separation (master
key belongs with the Danger-Zone-adjacent controls or behind the account menu, not in
the always-visible header row), and keep the red framing on the master entry only.

### G-2 🟠 God Mode lost its path to the live consoles
**Where:** facilitator/page.js:1336 comment — "Live-session consoles (**moved from God
Mode**)"; verified: zero references to `trading-floor`, `shockwave`, or `war-map`
anywhere in god-mode/page.js.
**What:** The consoles' server gates always pass for `god_mode`
(`_require_console_capability`), but the God Mode chrome now offers no navigation to
them. The owner running the backstage panel during a finale must remember three URLs
or keep a facilitator-portal tab open. Navigation should never require memorized URLs
for capabilities the role holds.
**Fix:** restore the three external links as a "Live Consoles" block at the foot of the
God Mode sidebar — same components, same `data-tooltip` truth conventions (Shockwave
keeps its DESTRUCTIVE framing). Pure chrome.

### G-3 🟠 The Shockwave console's crisis catalog is a hand-copied duplicate of the engine's
**Where:** shockwave/page.js:11–16 (four events with hardcoded labels and impact
strings "−$6.0M · −6 rep") vs backend `_SHOCKWAVE_EVENTS` (admin_router.py:4184–4189).
**What:** The numbers currently match. This is the same single-source-of-truth defect
that produced v1's F5 (stale round labels): the next engine rebalance desyncs the
console, and a facilitator picks a crisis based on impact numbers that are no longer
what fires. On a destructive control, drift isn't cosmetic.
**Fix (within constraints — no backend edits):** move the catalog to one exported
frontend constant co-located with a loud comment naming the backend dict, **plus a unit
test** (the repo already runs frontend tests: `__tests__/rival-intel.test.js` pattern)
that fails when the frontend constant and a fixture of the backend values diverge —
cheap tripwire, zero runtime change. **Proper fix (flagged for a backend cycle):** a
`GET /api/admin/shockwave/events` catalog endpoint; deferred, not smuggled in.

### G-4 ⚪ Dead router case
god-mode/page.js:916 `case 'glossary_editor'` has no corresponding sidebar item in
`GOD_MODE_SIDEBAR` (verified) — unreachable except by stale deep-link state. Same
class as v1 G7's `cohort_orchestration`. Delete the case or reinstate the item;
if deleted, confirm no `setActiveTab('glossary_editor')` callers remain.

### G-5 ⚪ Master-password modal polish
The modal's success copy ("Store it securely — it is not shown again") is good;
two small gaps: no caps-lock hint on a credential this consequential, and no
post-rotation reminder that other signed-in master sessions stay valid (or don't —
whichever `auth_jwt` actually does; verify before writing the copy so the UI doesn't
guess). Copy-only change either way.

---

## 4. Phased implementation plan

Same discipline as v1/v2, restated as invariants: **(1)** every phase touches only
admin-side files — never `hooks/useSimulation.js`, player `app/page.js`, or
player-cockpit components; **(2)** rendering-only phases land before anything that
wraps a mutation; **(3)** no phase changes which HTTP requests are sent, their
payloads, or their timing — the two explicit, gated exceptions (S4's rehearsal flag,
S5's backend-field items) are called out as such and ride behind your sign-off.

**Shared-component register for this pass:** `FacilitatorManager` and
`CreateCohortModal` render on **both** dashboards (God Mode registry + facilitator
portal + Dashboard Home) — every S2/S3 edit to them gets dual-surface testing.
`DashboardHome` is facilitator-only but role-polymorphic (facilitator / lead /
super_admin / project_admin) — test all four roles. The consoles are standalone
routes; their only shared dependency is the leaderboard endpoint.

---

### Phase S0 — Baseline (no changes)
Branch `ux/v3-phase-S1`…; screenshots of both dashboards **plus the three consoles in
all states** (off/error/live/closed); HAR capture walking every surface (the
regression oracle for "data flow unchanged"); player smoke (`test_api_flow.py`,
unmodified) green; backend pytest green count recorded; two-browser capture of one
real shockwave + one bell ring on a **throwaway cohort** — this is the
payload/behavior reference S3 and S4 diff against.
**Rollback:** n/a.

### Phase S1 — Chrome truth & routing hygiene (lowest risk: rendering only)
**Scope:** G-2 (console links back into God Mode sidebar) · G-4 (dead case) ·
F-5 (quick-action/alert filtering via `canAccessTab` + project_admin home variant) ·
F-8 (derive shortcut keys from `FILTERED_SIDEBAR`) · F-9 (switch labels, split error
states, war-map round range) · F-5's `ROLE_HIERARCHY` project_admin entry · G-5 copy.
**Why first:** no mutations touched; pure display and navigation-source-of-truth work.
**Testing checklist:**
- [ ] HAR diff vs S0: identical endpoint set, methods, payloads, cadences.
- [ ] Role matrix (facilitator / lead / super_admin / project_admin): Dashboard-Home
      quick actions show only reachable tabs; project_admin home leads with Create
      Cohort + Registry; no 🔒 panel reachable from a home-screen button.
- [ ] God Mode sidebar shows the three console links; tooltips match the facilitator
      side verbatim; Shockwave keeps the destructive framing.
- [ ] Ctrl+1…N toggles exactly the visible groups for each role; `?` sheet shows the
      derived count.
- [ ] Consoles: expired-cookie test shows the sign-in remedy message; backend-down
      test shows the unreachable message; war-map with cohorts at R3/R6 shows the range.
- [ ] Participant watch: `git diff --stat` whitelist — no player files; player smoke green.
**Rollback:** revert the phase commit; no persisted state or storage-format changes.

### Phase S2 — Feedback completeness on the new mutation surfaces (additive UI)
**Scope:** F-3(b)(c) (ring-bell failure surfacing + reopen affordance — **not** the
confirm yet) · F-4 (Excel pre-flight confirm + checklist-weight result panel) ·
G-1 (header disambiguation/relocation of the master-key entry).
**Boundary discipline:** every fetch keeps its URL, method, and body; only what
happens *around* success/failure changes. `FacilitatorManager` edits tested on both
dashboards.
**Testing checklist:**
- [ ] Bell with backend stopped → board stays live, named failure, retry visible;
      players see nothing (two-browser). Bell with backend up → behavior and payload
      identical to the S0 capture, including the staggered reveal and confetti.
- [ ] "Reopen board" restores the live poll (dev-tools: 5s cadence resumes) without
      any POST.
- [ ] Excel drop → pre-flight confirm; cancel sends nothing (network tab); accept →
      request identical to S0; result panel row counts equal the server response;
      CSV path pixel-identical to today.
- [ ] God Mode header: master-key entry no longer adjacent to 🔑; both modals still
      reachable; a first-time user asked to "change your password" (hallway test)
      does not open the master dialog.
- [ ] Participant watch: none of these components render player-side; player smoke anyway.
**Rollback:** revert; all additive.

### Phase S3 — Targeting integrity on destructive consoles (highest care in this pass)
**Scope:** F-1 (shockwave: no auto-select, visible prefill from the dashboard
selection, tier-2 impact-preview confirm with cohort name + team count + impact) ·
F-3(a) (bell: tier-2 confirm with the all-cohorts blast radius) · F-6 (one role
resolution for `CreateCohortModal` at both call sites + explicit project_admin branch,
capabilities verified against `admin_router.py` first).
**Risk & isolation:** this changes *which target* flows into a destructive request —
the one place a UI bug hits the wrong cohort. Mitigations: the confirm gates are
in *front* of unchanged requests (invariant: confirm-then-execute produces a request
byte-identical to S0; cancel produces none); the shockwave target is never submitted
without the cohort name having been rendered inside the confirm the user clicked;
each of the three items is its own commit.
**Testing checklist:**
- [ ] Shockwave with nothing selected: no cohort pre-picked, Detonate disabled,
      chooser shown; select cohort B while dashboard selection is cohort A → console
      clearly shows B (prefill is a suggestion, not a binding).
- [ ] Confirm shows team count that matches the server's `teams_hit` in the response
      after firing (throwaway cohort).
- [ ] Cancel at the confirm: zero network requests. Confirm: URL/method/body identical
      to the S0 shockwave capture.
- [ ] Bell confirm states the all-cohorts scope; with two cohorts live and one player
      in each connected, both player screens receive the overlay exactly as in S0
      (the honest-copy check: the UI now says what S0 silently did).
- [ ] `CreateCohortModal` role matrix at both entry points: project_admin sees the
      same (new) variant from Dashboard Home and Registry; super_admin unchanged;
      base facilitator unchanged; creation payloads for an identically-filled form
      diff clean against S0.
- [ ] Participant watch: run a full round on a live cohort while a shockwave hits a
      *different* throwaway cohort — the live cohort's players see nothing and
      `next_unlock_at`/round state are untouched.
**Rollback:** revert per-commit (shockwave / bell / modal are independent). Because
payloads are unchanged, a revert cannot leave server state inconsistent.

### Phase S4 — Surface rehearsal mode (the one new request variant — explicitly gated)
**Scope:** F-2. One button, one additional body field (`rehearsal: true`) on the
existing shockwave endpoint, preview rendered from the POST response.
**Why isolated:** this is the only item in the plan that makes the UI send something
it never sent. The server contract pre-exists and is documented as a no-op on game
state; the phase exists so that claim is *proven*, not assumed.
**Testing checklist:**
- [ ] Rehearse against a throwaway cohort with a player connected: player screen shows
      **nothing**; player `/dashboard` payload before/after is byte-identical;
      treasury/reputation unchanged in the leaderboard.
- [ ] Server audit trail shows `shockwave_rehearsal` (it does this today — verify the
      entry so rehearsals are attributable).
- [ ] Rehearse then Detonate: the real detonation is unaffected by a prior rehearsal
      (impact equals the S0 capture).
- [ ] 403 path (profile with `shockwave_enabled` off): rehearse shows the same named
      error the detonate path shows.
**Rollback:** revert removes the button; no residue (rehearsal writes no state).

### Phase S5 — Deferred items requiring backend touches (do not fold into S1–S4)
**Scope, each behind explicit sign-off, one endpoint/field per commit, additive only:**
F-7 (`can_create_cohorts` in the auth payload → button truth) · G-3 proper fix
(shockwave catalog GET) · F-4 proper fix (`dry_run` on bulk-upload for Excel preview
parity). Until then their S1–S3 mitigations stand (modal-surfaced rejection; drift
tripwire test; pre-flight confirm).
**Testing checklist (if executed):** backend pytest count unchanged +1-per-new-test;
auth payload diff shows only the added field; old frontends (pre-S5) still work against
the new backend (additive compatibility check); player smoke untouched.
**Rollback:** revert backend and frontend commits independently — the frontend must
degrade gracefully when the field/endpoint is absent (feature-detect, never assume).

---

## 5. Standing test protocol (every phase)

1. `git diff --stat <phase-base>` against the path whitelist — no `backend/` (except
   S5 by sign-off), no `useSimulation.js`, no player components; shared-register files
   trigger dual-surface checks.
2. Backend pytest at the S0 green count.
3. Player E2E smoke (`test_api_flow.py`, never edited to accommodate a UI change).
4. HAR contract diff for both dashboards **and all three consoles**; additions must
   appear in the phase notes (only S4 and S5 may add anything).
5. Two-browser rehearsal: facilitator + player through two rounds, exercising the
   phase's surfaces; the player screen must show no unprompted change — with S3/S4,
   specifically watch during shockwave confirm-cancel, bell confirm-cancel, and
   rehearsal.

---

## 6. Priority order (if you do nothing else)

1. **S3's F-1 + F-3(a)** — the two destructive consoles currently combine wrong-target
   defaults with blind confirms; this is the "override lands on the wrong cohort"
   failure mode v1 eliminated elsewhere, alive on the highest-impact controls.
2. **S2's F-3(b)** — the projector claiming "MARKET CLOSED" after a failed broadcast
   is the dashboard lying at the most public moment a session has.
3. **S4 (F-2)** — rehearsal is already built and paid for server-side; surfacing it
   converts the scariest control into a teachable one.
4. **S1's F-5/F-6** — before the next time a project_admin provisions a real programme.

---

*All file/line references checked against the working tree on 2026-07-11 (HEAD
`141a331`). Backend files were read only to verify UI truthfulness; no backend change
is proposed outside the explicitly gated Phase S5. Happy to expand any phase into a
per-file change list, or spec the shockwave confirm / rehearsal preview components next.*
