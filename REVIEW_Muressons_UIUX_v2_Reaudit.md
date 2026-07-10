# Muressons — UI/UX Re-Audit v2: God Mode & Facilitator Screens

*Second systematic pass, run against the CURRENT tree (post Phases 1–6 + your
subsequent changes). Process per the brief: code first, then hierarchy/state
mapping, then friction points with concrete fixes. Review and plan only — no
code changed. Same hard constraints: simulation logic, scoring, data flow and
the participant experience stay functionally identical.*

**Severity key:** 🔴 blocks facilitator · 🟠 slows facilitator · ⚪ cosmetic

---

## 0. Status of the v1 findings — verified in the current tree

All 21 v1 findings (F1–F12, G1–G9) were implemented across commits `559f8d2`,
`fc771ec`, `2095ef9`, `18d7bdd`, `80a854c`, `d422693` and verified intact
today: the single status poller + tri-state header, unified CohortSelector,
WS reconnect + liveness chip, tiered ConfirmModal on every destructive path,
per-pill toggle feedback with blast-radius confirms, truthful per-cohort
Interview reads, Session Setup grouping, shortcut sheets, and the mobile
toggle are all present (`useGodSystemStatus` ×2 refs, `canAccessTab`/
`CohortSelector`/`useConfirm` ×15 refs in the facilitator page). Your
uncommitted edits touch the portal/layout files, not the two dashboards.

So this pass goes where v1 didn't: the mid-session *workhorse panels* a
facilitator actually lives in during a round — the Leaderboard, the
Teleprompter, cohort creation, and messaging — plus an honest check of chrome
the earlier phases added.

---

## 1. New findings — Facilitator screen

### V2-1 🟠 The Leaderboard cannot sort or search — and its tooltip says it can
**Where:** `LeaderboardMatrix.js` (360 lines): 18 columns (Round, TV, Cash,
Synergy, Reputation, Bonus, Stakeholder, Materiality, Learning, NCD, Social
License, Talent, Shadow Board, Practice, Actions…), zero `sort` state, zero
search input. `sidebarConfig.js` tooltip: *"Sortable and searchable with
delete/reset controls."*
**Why it matters:** this is the primary triage surface ("who needs help?").
Finding the lowest-reputation team mid-round means visually scanning an
18-column matrix — exactly the task sorting exists for. And the tooltip
promising it is the same truth-vs-UI defect class as v1's G7: the interface
documents capabilities it doesn't have, which erodes trust in every other
tooltip.
**Fix:** client-side, display-only interactivity — clickable column headers
(asc/desc, sort indicator, keyboard-operable), a search box filtering by
cohort/player name, and column triage: the 7 decision-relevant columns
(Round, Treasury, Reputation, Synergy, TV, Talent, Actions) always visible,
the assessment columns (Stakeholder/Materiality/Learning/Bonus/Shadow Board)
behind a "More metrics" toggle. Pure render-layer: same leaderboard array,
same fetches, rows reordered/hidden client-side only.
**Rejected quick fix:** editing the tooltip to stop claiming sortability.
That restores honesty but leaves the actual triage friction untouched — the
tooltip promised the right feature; build it.

### V2-2 🟠 The Teleprompter is set in dashboard type, not podium type
**Where:** `FacilitatorTeleprompter.js` — dominant font sizes are 0.65–0.82rem
(21 uses of 0.68rem); no text-size control, no presentation mode.
**Why it matters:** this component's entire job is being read aloud, at a
podium, at arm's length-plus, mid-session. Caption-sized talking points force
the facilitator to lean into the laptop — the posture the teleprompter exists
to prevent. (The good bones are already there: per-cohort sync, round
selector, checkable talking points, notes.)
**Fix:** a presentation-mode toggle in the teleprompter header — scales the
script content (talking points, discussion prompts, round banner) via a CSS
custom property (e.g. `--tp-scale: 1 / 1.3 / 1.6`), persisted in
localStorage, with the intel side-panels unscaled. Optionally a true
fullscreen (`requestFullscreen`) for projector use. Display-only; the
scripts, checkpoint state, and fetches are untouched.
**Rejected quick fix:** bumping the base font sizes globally. That degrades
the two-column layout's density for prep use; reading distance is a *mode*,
not a constant.

### V2-3 🔴 Cohort creation can half-configure a live cohort — with one string of regret
**Where:** `CreateCohortModal.js` (2,265 lines). Creation/edit runs a core
session request, then a *chain* of sub-configs (`runSubConfig`: Visibility,
Pedagogical Settings, Side Tracks, Pacing, Switchboard/cohort-settings…).
Each failure is caught and appended to `configWarnings`; at the end the user
gets one concatenated error string — *"Cohort updated, but some settings
failed: Pacing: HTTP 500 | Side Tracks: …"* — and, on the edit path, when
warnings exist `onCreated` is never invoked. There is no per-item retry: the
only recovery is re-running the whole form. The create and edit paths carry
**duplicated copies** of this chain that have already drifted (different
warning formats).
**Why it matters:** this is session *setup*, and partial failure is silent in
effect: the cohort exists and will run — with default pacing or missing side
tracks — while the facilitator's mental model says "configured." That's a
class-blocking defect discovered mid-round ("why is R3 already unlocked?").
**Fix:** (a) a setup-integrity result panel: after submit, render the
sub-config chain as a checklist (✓ Pedagogical Settings · ✗ Pacing — Retry),
with per-item retry buttons that re-PUT only the failed payload (identical
endpoint/body — no new contract); (b) block the modal's success-close while
any item is failed, with an explicit "keep as-is" escape; (c) unify the
duplicated create/edit chains into one function so the two paths cannot
drift. The cohort creation order and payloads remain byte-identical.
**Rejected quick fix:** turning the warning string into a prettier toast.
Same information, same dead end — the underlying problem is *unrecoverable
partial state*, and only per-item retry addresses it.

### V2-4 🟠 Broadcast failure is invisible (the panel Phase 2 missed)
**Where:** `BulkMessaging.js` — send handler: `if (res.ok) { …reset form,
refresh history }` with **no else branch** and `catch { /* error */ }`.
History fetch failures likewise silent.
**Why it matters:** identical failure class to v1's F10, missed because the
component wasn't in the v1 mutation inventory. Mid-session: facilitator
announces "check your mailbox," the send 500'd, nothing happened, and the
form *didn't clear* — the only symptom is ambiguity. `SwipeFile.js` has
partial catch handling; it needs the same audit.
**Fix:** apply the established Phase-2 flash pattern (`flash(msg, ok)`,
red/green, failure names the action and preserves the composed message);
inventory-sweep the remaining admin mutation sites (SwipeFile, StudentBonuses,
InterventionConfig, AutoPauseConfig) for the same missing else-branch.

### V2-5 ⚪→🟠 The bottom action bar can overflow at laptop widths
**Where:** facilitator page fixed bottom bar (`display:flex, gap:1rem`, no
`flex-wrap`) now carries: role badge + Live/Reconnecting chip + CohortSelector
+ selection text + 3 quick actions + shortcut hint. On ~1280px screens (the
projector/laptop class the sim runs on) the Undo button or hint can clip
off-screen — and Phase 3/4 additions made the bar the primary control strip,
so clipping is no longer cosmetic.
**Fix:** `flex-wrap: wrap` with sensible order (selector + actions first),
hide the shortcut hint below ~1200px (it's duplicated in the `?` sheet), and
let the selection text truncate with ellipsis + title. Mirror check on the
god-mode top bar, where the breadcrumb and CohortSelector share one
unwrapped row.

---

## 2. New findings — God Mode screen

### V2-6 🟠 Blast-radius numbers can be one poll stale
**Where:** `GodModeStatus.togglePill` and freeze confirms build their impact
line from `status?.total_players` — polled every 10s.
**Why it matters:** the confirm says "affects 12 players" while 14 are
connected. For freeze this is informational; for a mid-round engine toggle
the number is the decision input.
**Fix:** on opening a blast-radius confirm, kick `onRefresh()` and render the
count live from the store (the modal already re-renders on prop change), with
a "as of HH:MM:SS" suffix using the existing `lastSuccess`. No new endpoints.

### V2-7 ⚪ Leaderboard tooltip class — sweep all sidebar tooltips against reality
v1 fixed two lying tooltips (G7, timeline); V2-1 found a third. The honest
fix is systemic: a one-time audit pass of all 40+ tooltips in
`sidebarConfig.js` against what each tab renders, plus a comment convention
("tooltip must describe what the tab RENDERS") at the top of the config —
cheap insurance against the next drift.

### V2-8 ⚪ ShortcutSheet lists shortcuts the Danger Zone-era code no longer needs verified
Both dashboards' sheets are static arrays. If a binding changes (as Ctrl+B →
Ctrl+Shift+B did), the sheet is a second place to update. Fix (small): derive
the sheet contents from a single exported SHORTCUTS constant per page used by
both the handler and the sheet.

---

## 3. Phased implementation plan (remainder)

Same discipline as before: one commit per phase, endpoint-contract diff
(only R3 legitimately adds calls — retries of identical payloads), esbuild +
ESLint + production build in-sandbox, player smoke after every phase, revert
= rollback. No backend edits anywhere.

### Phase R1 — Feedback completeness (lowest risk)
V2-4: Phase-2 flash pattern into BulkMessaging + audited sweep of SwipeFile /
StudentBonuses / InterventionConfig / AutoPauseConfig; V2-6 fresh-count
confirms; V2-7 tooltip truth sweep; V2-8 single-source shortcuts.
**Test:** kill backend → every send/toggle shows a named red failure and
preserves user input; broadcast success still clears the form and lands in
player mailboxes exactly as before (two-browser check); tooltips spot-checked
against tabs. **Rollback:** revert; pure additive UI.

### Phase R2 — Leaderboard triage (display-only interactivity)
V2-1: header sorting, name search, core/extended column split.
**Test:** sort/search never triggers a network request (dev-tools clean);
row selection → session tools still target the right session after sorting
(the selection is by session_id, not index — verify); delete/practice
controls operate on the correct row post-sort; 18-column data unchanged
under "More metrics".
**Rollback:** revert restores the static table.

### Phase R3 — Cohort setup integrity (the one 🔴)
V2-3: unified sub-config runner + checklist result panel + per-item retry +
guarded close.
**Test:** force a sub-config 500 (stop backend mid-chain) → checklist shows
the exact failed item; retry re-sends the identical payload (HAR-compare);
success path byte-identical to today (same order, same payloads); a cohort
created fully green behaves identically in a two-browser round.
**Rollback:** revert; creation reverts to the warning-string behaviour.

### Phase R4 — Teleprompter presentation mode
V2-2: scale toggle + persistence (+ optional fullscreen).
**Test:** scale affects script panes only; checkpoints, notes, cohort/round
selectors, and all fetch behaviour unchanged; localStorage survives reload;
1280×720 projector check at 1.6×.
**Rollback:** revert; default scale is today's rendering.

### Phase R5 — Chrome overflow hardening
V2-5: bar wrap/truncation on both dashboards + god-mode top-bar wrap.
**Test:** 1280 and 1024 widths — all quick actions reachable, selector
usable, nothing clipped; full-width unchanged pixel-wise.
**Rollback:** revert.

*Ordering rationale: R1 completes an already-proven pattern; R2 is
interactive but read-only; R3 wraps mutations (highest care, isolated); R4–R5
are contained polish. The v1 standing protocol (whitelist, pytest 967,
player smoke, build, two-browser rehearsal checklist) applies to every phase.*
