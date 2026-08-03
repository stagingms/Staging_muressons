# Implementation — second pass, 2 Aug 2026

Follows `IMPLEMENTATION_2026-08-02_UX_Audit.md`. Covers audit item **#18** and
the three partials (**#6**, **#7**, **#9**), plus one drift I introduced in
pass 1 and have now closed.

**Verified: 1802 backend tests pass** (up from 1785 — 17 new team-seat tests),
6 skipped. All 23 touched/new frontend files parse clean under esbuild. Engine
untouched; the golden trace and simulation-integrity suites are unmodified and
green.

---

## #18 — One accessible Dialog primitive (CONTRACTUAL WCAG item)

**New: `frontend/app/components/Dialog.js`.** A *wrapper*, deliberately not a
redesign — it renders the overlay element and owns the accessibility behaviour
while every caller keeps its own className, inline styles and inner markup.
Adoption is a two-line change per modal and cannot alter layout.

Guarantees: `role="dialog"` + `aria-modal` + an accessible name (4.1.2, 2.4.6) ·
Escape closes **only the topmost** dialog via a module-level stack, so a nested
dialog doesn't collapse both · focus moves in on open · Tab/Shift+Tab cycle
**within** the dialog (2.1.2) · focus returns to the invoking element on close
(2.4.3) · background scroll locked, refcounted for nesting.

`dismissible={false}` covers modals the user must resolve rather than escape
(forced password change, the R1 stakeholder gate, the 84-field cohort form where
a stray Escape would discard everything).

Applied to all 8: `ConfirmModal` (which loses its bespoke Escape handler — the
primitive is a strict superset), `CFOOverrideModal`, `JoinCohortModal`,
`ChangePasswordModal`, `BalanceSheetModal`, `StakeholderMapModal`,
`UsernamePromptModal`, `CreateCohortModal`.

---

## #7 — Team seats **(scope corrected: teams are real)**

The pass-1 reading was wrong. Corrected model, built additively:

> A team is **up to 6 people**: one **driver** who enters and commits, plus up
> to five **observers** who watch the same live board read-only.

- **Driver** holds the team credential (`MUR-004`) — unchanged. One session, one
  company. The credential *is* the seat, so handing over to another member is
  just signing in as `MUR-004` on their laptop.
- **Observer** holds the team's shared view code (`MUR-004-VIEW`), resolves to
  the **same session**, and is refused by every mutating endpoint.

**No new session, no new game state, no engine change** — an observer is a
read-only identity pointed at an existing session.

**Security posture is fail-closed.** `_assert_player_owns_session` (used by all
28 player routes) rejects observers *by default*; a route must opt in with
`allow_observer=True`. Exactly one route has — `GET /{id}/dashboard`. Any route
added later is driver-only without anyone having to remember.

Backend: `router.py` (view-code helpers, guard, observer login path with its own
password check before the join delegation), `admin_router.py`
(`POST/GET /players/{id}/team-seats`, cap 6, credential returned once).
Frontend: `useSimulation.isObserver` (persisted so a refresh never briefly shows
a writable cockpit), observer banner + disabled commit control + blocked
selection paths in `ExecutiveCockpit`, `preflightCommit` guard in `page.js`,
"👥 Seats" control in `PlayerRegistry`, corrected join-screen copy.

**Reverted from pass 1** (they were based on the wrong premise): "Waiting for
Other Teams", "X/Y teams committed", CohortPulse "Team" column headers.

**`team_consensus` restored as a real input** (TEAM-2): a four-way selector —
Unanimous / Majority / Split / Facilitator call — in the review modal, written
to the decision audit log. It was a hardcoded `'majority'`; it is now the
driver's actual answer, which makes *"how did you decide?"* answerable from data
in the debrief.

New: `backend/tests/test_team_seats.py` — 17 tests pinning view-code parsing,
fail-closed refusal, the single opted-in read, cross-team isolation, the seat
cap, and a tripwire asserting **`engine.py` never learns the words** `observer`
/ `view_code` / `team_view`.

---

## #6 — Undo Round co-located

Advancing a round lives in Live Classroom; its inverse was two sidebar
categories away, so a facilitator who over-advanced in front of a cohort had to
change context to find the fix. `undo_round` moved into **Live Classroom**,
directly after Manual Overrides.

`filterSidebarForRole` gained `showDisabled`: an item below the caller's role
tier now stays **visible but inert**, with the reason on hover (*"Lead
facilitator or above can roll a round back — ask them to undo it for this
cohort"*), instead of vanishing. A base facilitator can now see the capability
exists and who to ask. Presentation only — the backend guard is unchanged and
remains the security boundary.

---

## #9 — Auto-commit markers in the timeline and exports

A round the server auto-committed (Option B, $1/BU) was indistinguishable from a
deliberate conservative strategy once it left the player's screen — a grading
blind spot.

`GET /api/admin/leaderboard` now returns `auto_committed_rounds`,
`auto_committed_count` and `auto_committed_now`, scanned from round history
already fetched for the sparkline (no extra query, read-only over an engine
flag). Surfaced in **RoundTimeline** (amber ring on the affected dots + a `⏱n`
badge per team) and in **ReportsExport** — two new CSV columns
(*Auto-Committed Rounds*, *Auto-Committed Count*), the field in the JSON export,
and an on-screen `⏱ auto×n` marker so it isn't export-only.

---

## Drift closed (self-reported from pass 1)

In pass 1 I removed the 10 inert visibility keys from
`frontend/app/config/analyticsRegistry.js` but left them in
`_analytics_visibility` in `backend/admin_analytics.py`, against that file's own
"add keys in both places in the same commit" rule. Harmless (the setter only
writes keys the backend knows) but real. The orphans are now removed with a
comment recording why.

---

## Files touched

Backend: `router.py`, `admin_router.py`, `admin_analytics.py`,
`tests/test_team_seats.py` (new).
Frontend: `components/Dialog.js` (new), `ConfirmModal`, `CFOOverrideModal`,
`JoinCohortModal`, `ChangePasswordModal`, `BalanceSheetModal`,
`StakeholderMapModal`, `UsernamePromptModal`, `CreateCohortModal`,
`ExecutiveCockpit`, `CohortPulse`, `PlayerRegistry`, `ReportsExport`,
`RoundTimeline`, `hooks/useSimulation.js`, `page.js`,
`admin/facilitator/page.js`, `config/sidebarConfig.js`,
`config/analyticsRegistry.js`.

## Still open

1. **WCAG conformance pass.** Dialog semantics, keyboard operability and
   contrast are now fixed, but source reading is not an audit. Plan the real
   thing — assistive-tech testing, ending in a VPAT — as its own workstream.
2. **`team_consensus` DB column** is still `NOT NULL DEFAULT 'majority'`. Now
   that the field carries a real answer this matters less, but a Postgres
   migration would let "not recorded" be distinct from "majority".
3. **Observers are anonymous** by design (one shared code per team). If
   attendance or per-person grading ever needs names, that becomes named
   observer seats — a roster change, not an architecture change.
4. Audit items **#13** (live-round sidebar mode), **#15** (timer honesty),
   **#19** (cohort-creation wizard), **#20** (token consolidation), **#21**
   (consequence-chain coverage), **#22** (co-facilitator access) remain
   unstarted.
5. `npx next build` still not run here (no `node_modules` in this sandbox) —
   run it before the next class, or let the Railway Docker build be the gate.
