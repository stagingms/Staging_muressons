# Implementation — third pass, 2 Aug 2026

Closes the last six audit items: **#13, #15, #19, #20, #21, #22**. Every
numbered recommendation in `AUDIT_UX_Product_2026-08-02.md` is now either
implemented or explicitly declined with a reason.

## Verification — including the gate that was previously blocked

- **`npx next build` PASSES.** `✓ Compiled successfully in 47s`, all 11 static
  pages generated including the new `/admin/projector`. This is the check the
  earlier passes could not run (no `node_modules` in the review sandbox). One
  caveat: the sandbox cannot reach `fonts.googleapis.com`, so `next/font` fails
  there and only there. I confirmed compilation by temporarily stubbing the two
  font imports in `layout.js`, building, then restoring the file — verified
  byte-identical afterwards by `diff`. Railway has network access, so the real
  build will resolve the fonts normally.
- **Backend: 1802 passed, 6 skipped.**
- **Frontend jest: 32 suites, 800 tests, all passing** — including ~500 new
  assertions from this pass. That number also reflects a pre-existing failure I
  caused in pass 1 and have now fixed (see below).

---

## #13 — Live-round sidebar mode

34 facilitator tabs is the wrong surface area for someone teaching a room. A
`liveRound: true` flag now marks the **12** tabs a facilitator actually reaches
for mid-round (Command Center: dashboard_home, timeline, teleprompter,
leaderboard · Live Classroom: registry, session_viewer, impersonate, swipe_file,
broadcast, manual_override, undo_round, custom_black_swan). `dry_run` and
`intervention_config` are deliberately excluded as setup decisions.

A persisted toggle (`🎬 Live Round` / `📚 All Tabs`, `aria-pressed`, survives
refresh) filters the sidebar **after** role filtering, so it never widens
access and the `_locked` signpost items from pass 2 survive intact. The
edge case is handled: if the active tab is not in the live subset, the workspace
is **not** blanked — it keeps rendering with a note and a one-click return. The
four projector/console links stay visible in both modes.

## #15 — Honest timer

`DecisionPressureTimer` used to `return null` for both "no pacing yet" *and*
`mode === 'free'`, so in its own default mode the player had **no deadline
surface at all** — silently absent rather than honestly absent. It now renders
in every mode: countdown when timed, `🎬 Facilitator paces this round` in
manual, `∞ No time limit this round` in free, each keeping the X/Y commit tally.
The rule applied: never imply time pressure that isn't real, never leave the
player guessing whether a clock is running.

Second half of the fix: the round briefing is an **architectural early return**
that unmounts the whole cockpit tree, so a timed round could run down entirely
while a player read the briefing with no clock on screen. The page now threads a
pacing chip into the briefing via a new `pacingChip` prop.

## #19 — Server-side cohort setup + pre-lock preview

Creating a cohort was one create call followed by **up to ten** sequential
PUT/POSTs from the browser; any one could fail after the cohort existed, leaving
a half-configured cohort and a hand-worked repair panel — at the moment of
maximum irreversibility.

New `POST /api/admin/cohort/{id}/apply-setup` moves that chain server-side: one
request, applied in order in-process, returning a per-section report. Two things
the browser chain could not offer:

1. No partial state from a dropped connection mid-chain.
2. **`dry_run: true` applies nothing and returns exactly what would change** —
   the pre-lock preview the audit asked for.

Honest scoping: this is deliberately *not* a database transaction. The sections
write to different stores (session metadata, cohort_settings, pacing), so the
guarantee is "one round trip, ordered, fully reported", not ACID — and the
report names exactly what applied, so recovery is targeted rather than guesswork.
The client gains `previewSetup()` and `buildApplyPayload()`; the legacy chain
remains as a fallback so a backend without the new route is never a regression.

## #20 — Token drift ratchet (not a sweep)

The audit said measure the drift *and* don't fix it with a blind regex — and
this repo has the scar tissue: `globals.css` carries an entire "Light Mode —
Inline Style Color Compatibility Shim" produced by a previous sweep, and
CLAUDE.md states the rule outright.

So the deliverable is a **ratchet**, modelled on the repo's existing tripwires
(`test_role_hierarchy_sync.py`, `shockwave-catalog.test.js`):
`frontend/__tests__/design-token-drift.test.js`.

- Counts (rawHex 1250 · rawPx 5034 · box-shadow 395 · font-size 1805) are
  baselined at today's values with 2% headroom for formatting churn. **New drift
  fails the build**; migrating a file lowers the number, and the baseline is
  lowered in the same commit. The number only moves one way.
- Two sharper rules ratcheted **by file**: the three semantic hexes whose
  light-mode values were corrected for WCAG on 2026-08-02 (`#059669`,
  `#d97706`, `#0891b2`) may not appear in any file outside an explicit 18-file
  legacy list, and z-index above `--z-top` (9000) may not appear outside a
  12-file legacy list. A **new** file breaking either rule fails immediately.
- A further test fails if a listed file has been migrated but left on the list,
  so the boundary tightens automatically instead of rotting.

## #21 — Complete the consequence chain

`ConsequenceReplay` built its "why did this happen" explanation from a hardcoded
key list and then truncated to the first few flags, so any engine effect not on
that list was **silently absent** and the gap was invisible. This was the
biggest pedagogical hole in the player experience.

New `consequenceCatalog.js`: **239 entries** across eight engine families
(talent/burnout, climate/carbon, finance/covenant, stakeholder/social-licence,
supply chain, black swan/systemic risk, regulatory, governance) each with a
plain-English `explain()`. The replay now walks **every** truthy flag; unknown
keys still render with a humanised label rather than being dropped, and where
the engine emitted a sibling `*_message`/`*_narrative` string that prose is used
verbatim. `IGNORED_KEYS` is an explicit, commented list of genuine bookkeeping
(94 keys + two prefix rules) so exclusion is a documented decision. The `slice(0, 6)`
truncation is gone.

Notable finding: the old code checked `events.cyclone_loss`, **a key the engine
never emits** — that node could never have fired. Physical climate damage lands
as `climate_event_struck` / `actual_damage` / `climate_resilience_factor`.

## #22 — Co-facilitator / TA read-only access

Ownership stays **single** — a live run needs one unambiguous accountable
operator. What is new is `can_observe_session`, a strictly READ predicate
satisfied by the owner, admins, and anyone on the cohort's new
`co_facilitator_ids` list. `owns_session` is untouched, so **every existing
write guard stays closed to co-facilitators with no change at those ~30 call
sites** — the fail-closed property.

Endpoints: `GET/POST/DELETE /api/admin/sessions/{id}/co-facilitators`, max 3 per
cohort, granting restricted to the owner, `project_admin` explicitly refused (it
is a provisioning role off the run ladder), both mutations audit-logged. The
leaderboard now includes observed cohorts flagged `is_observed`. A
co-facilitator attempting a write gets a message naming their actual standing
rather than a flat denial.

This replaces the current arrangement, which is handing over the owner's
credentials — something `must_change_password` actively fights.

## Pass-1 regression fixed

`__tests__/predict-modal-review.test.js` pinned the old prediction-modal labels
("← Go Back", "Skip & Commit") which my §7.4 rename in pass 1 changed. Test
realigned to the new copy, with its header rewritten to explain *why* the labels
changed (the escape hatch and an irreversible commit shared a visual class and
the word "Skip" — a misclick trap). Full jest suite is green.

---

## Files touched

**Backend:** `admin_shared.py`, `admin_router.py`.
**Frontend:** `config/sidebarConfig.js`, `admin/facilitator/page.js`,
`components/DecisionPressureTimer.js`, `components/RoundBriefing.js`,
`components/CreateCohortModal.js`, `components/ConsequenceReplay.js`,
`components/ConsequenceReplay.module.css`, `components/consequenceCatalog.js`
(new), `page.js`, `__tests__/design-token-drift.test.js` (new),
`__tests__/consequence-catalog.test.js` (new),
`__tests__/predict-modal-review.test.js`.

## Still open — deliberately

1. **A real WCAG conformance pass.** Dialog semantics, keyboard operability and
   contrast are fixed and now ratcheted, but source reading is not an audit.
   Assistive-tech testing ending in a VPAT is its own workstream.
2. **`team_consensus` DB column** remains `NOT NULL DEFAULT 'majority'`; making
   "not recorded" distinct needs a Postgres migration.
3. **CreateCohortModal's 84 `useState` hooks and 7 accordions** are unchanged.
   #19 removed the *failure mode* (partial config) and added the preview; the
   form itself is still a form. A staged wizard is a genuine redesign and should
   be specced, not slipped in.
4. **Token migration itself** has not started — the ratchet holds the line so it
   can be done file by file, on a real screen, as the audit required.
5. **Per-BU dynamic flag families** (`talent_penalty_applied_<bu_id>` etc.) render
   through the humanised fallback rather than bespoke copy. A suffix matcher is
   the natural extension point if you want per-BU wording.
