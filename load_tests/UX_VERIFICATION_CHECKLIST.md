# UX & robustness verification checklist (audit #13)

These checks need a **running app + a browser** (and, for a couple, two clients),
so they can't be automated in CI the way the backend tests are. Run them against
a staging deploy before a real 500-user session. The one automatable slice —
the two-users-commit-at-once race — is covered by
`backend/tests/test_concurrent_commit_race.py`.

Mark each PASS/FAIL and file anything that fails.

## Facilitator: intervene in ≤ 2 clicks
1. Open the facilitator dashboard on a live cohort.
2. From the landing view, count clicks to: (a) freeze the room, (b) unlock the
   next round for one team, (c) send a broadcast/shockwave to one team.
- **Pass:** each is reachable in ≤ 2 clicks. **Fail:** if any needs 3+ — add a
  per-team quick-action row on `dashboard_home` (audit §5.2).

## Facilitator: all teams' status at a glance
- On one screen, every team's current round + "committed / not committed" is
  visible without scrolling or switching tabs. (The "X of Y teams committed"
  badge exists; confirm per-team granularity.)

## Player: responsive 1280 → 1440 → 1920
1. Load the player board at browser widths 1280, 1366, 1440, 1920.
2. At each: KPI belt, canvas stage, and the primary commit CTA are all visible
   and reachable **without horizontal scroll**.
- **Pass:** decision flow usable at all widths. **Fail:** note the breakpoint.

## Player: next action is always obvious
- At each round stage, the single most prominent element is the required next
  action (per the one-slot rule in `CLAUDE.md`). No ambiguity about what to do.

## Player: draft survives a refresh
1. Enter a round, change allocations/sliders, **do not commit**.
2. Hard-refresh the browser.
- **Pass:** the in-progress values are restored (autosave/`save-decisions`).
  **Fail:** add an explicit local draft cache (audit §3.1).

## Player: disconnect / rejoin mid-round
1. Mid-round, kill the network briefly, then restore it.
- **Pass:** the board reconnects (WS retry + REST poll) and shows a
  reconnecting/staleness indicator (see #11 `ConnectionBanner`), not a blank or
  stale-without-notice screen.

## Feedback after every action is immediate
- Commit, save, and facilitator pushes each produce an unambiguous UI response
  (spinner → result, sound, or banner). No silent no-ops.

## Accessibility (WCAG 2.1 AA smoke)
1. Run axe (or Lighthouse a11y) on the player board and the facilitator board.
2. Check: color contrast of danger/success KPI deltas, keyboard reachability of
   the commit CTA, focus visibility, and that interactive controls have labels.
- Record the axe score + any critical violations.

## Loading / error states
- Slow-network throttle: panels show skeletons/spinners, not blank frames.
- Backend down: a clear "server unreachable" state (not an infinite spinner or a
  silent stale board).
