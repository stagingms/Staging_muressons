# UX Phases 1–5 — Implementation Notes & Test Evidence

Branch: `ux/phases-1-5` (branched from `main`, which still holds all your other
uncommitted work — nothing of yours was committed except the 7 files I touched,
checkpointed first).

| Commit | Phase | Contents |
|---|---|---|
| `bc9b60d` | Phase 0 | Checkpoint of the pre-UX state of every file the phases touch |
| `559f8d2` | Phase 1 | Read-only truth fixes — G1, G4, F3, F5, F6, F11, G7, F1d |
| `fc771ec` | Phase 2 | Feedback & error surfacing — F10, F8, G6, G8 + `utils/adminFetch.js` |
| `2095ef9` | Phase 3 | Unified session selection — F2, G5 + `components/CohortSelector.js` |
| `18d7bdd` | Phase 4 | Admin-WS resilience — F1 (reconnect, poll fallback, liveness chip) |
| `80a854c` | Phase 5 | Destructive-action hardening — F4, G2, G3, F9 + `components/ConfirmModal.js` |

**Rollback:** each phase is one commit — `git revert <sha>` individually, or
`git reset --hard bc9b60d` to return to the exact pre-UX state. No schema, no
localStorage-format, and no endpoint changes anywhere, so reverts are complete
by themselves.

---

## Standing test protocol — evidence (run in sandbox, 2026-07-05)

### 1. Path whitelist ✅
`git diff --name-only bc9b60d..HEAD` — 13 files, all admin-side:

```
frontend/app/admin/facilitator/page.js      frontend/app/components/LeaderboardMatrix.js
frontend/app/admin/god-mode/page.js         frontend/app/components/RoundPacingControl.js
frontend/app/components/CohortSelector.js   frontend/app/components/RoundTimeline.js
frontend/app/components/ConfirmModal.js     frontend/app/components/SessionHealthDashboard.js
frontend/app/components/DashboardHome.js    frontend/app/components/UndoRound.js
frontend/app/components/GodModeStatus.js    frontend/app/config/sidebarConfig.js
frontend/app/utils/adminFetch.js
```

Zero matches for `backend/`, `useSimulation`, `RoundBriefing`, or any
player-cockpit component. No shared-register component was modified
(LeaderboardMatrix/UndoRound/RoundPacingControl render only inside the
facilitator dashboard; GodModeStatus/SessionHealthDashboard only inside God Mode).

### 2. Backend pytest ✅
`python3 -m pytest tests/ -q` → **961 passed, 0 failed** (Phase-0 documented
green count was 960; the extra test predates these phases). No backend file
was edited, and the suite confirms it.

### 3. Player E2E smoke ✅
The repo's own `test_api_flow.py`, **unmodified**, against a live backend on
the post-Phase-5 tree: solo-start → dashboard (4 BUs, $50M treasury,
multi_toggles) → pillar config → R1 crisis + 5 pillar decisions → commit
**201** → treasury/carbon KPIs update → TCFD/Biodiversity/Balance-Sheet/Board-Gov/
Supply-Chain engines all OK → R2 commit proceeds.

### 4. Endpoint-contract diff (static extraction of every fetch site) ✅
No endpoint, method, or payload changed in any phase. The only deltas are call-site
consolidation and declared frequency changes:

- **Phase 1:** `/api/admin/teleprompter` gains one *caller* (RoundTimeline — F5
  labels; same endpoint DashboardHome already used). `/god/system-status`
  callers 2 → 1 (G4 single poller: bar@15s + panel@10s became one 10s poll —
  a net *reduction* in backend load).
- **Phase 2:** `/api/admin/scaffolding-status` call sites 4 → 1 (one
  `refreshScaffolding()`; same 30s cadence + same WS triggers). Danger-Zone
  `GET /api/admin/sessions` now goes through `adminFetch` (adds
  `credentials:'include'` only). `X-Facilitator-Id` header dropped from the
  `global-settings` PATCHes — verified against `admin_router.py`: auth is
  `Depends(require_super_admin)` (JWT cookie); the header is read nowhere.
- **Phase 3:** contract byte-identical. Behavioral delta (intended): Round
  Pacing no longer auto-selects the first cohort, so its pacing GET fires only
  after an explicit selection.
- **Phase 4:** same WS URL/protocol; reconnect adds re-`connect` attempts after
  a drop plus a 30s leaderboard/scaffolding poll **only while disconnected**
  (zero steady-state change).
- **Phase 5:** `global-settings` PATCH call sites 4 → 3 (two identical inline
  handlers deduped into `togglePill`). All delete/rollback/freeze payloads
  byte-identical — only the confirmation gate in front changed; Cancel sends
  nothing.

### 5. Two-browser rehearsal ⚠️ — run this on your machine (can't be done in the sandbox)
Facilitator screen + player screen side by side, two rounds. Watch the player
screen for ANY unprompted change. Per phase:

- **P1:** With two cohorts at different rounds, Dashboard-Home directive card
  shows the *selected* cohort's round and names it; Round Timeline labels match
  the Teleprompter titles; stop the backend → God-Mode header shows
  **Unreachable** (never "0 · Optimal"), restart → recovers.
- **P2:** Toggle quiz difficulty with the backend stopped → red "NOT saved"
  appears and the UI does not flip; Danger Zone with an expired cookie shows
  "couldn't load", not "No cohorts active"; toggle Front Page off/on → player
  reveal honors it exactly as before.
- **P3:** Pick cohort A in the bottom-bar selector → Override/Message/Undo arm;
  every session tab and the Teleprompter agree; Pacing shows "— Select a
  cohort —" and fires **no** request until you choose; re-save the same pacing
  mode → only that cohort's player receives `pacing_override`, `next_unlock_at`
  unchanged.
- **P4:** Kill the backend 30s mid-session → chip flips to ⟳ Reconnecting,
  leaderboard updates via fallback; restart → ● Live, and God Mode's
  WS CONNECTIONS shows no leaked sockets after repeated bounces. **The player
  screen must never reconnect or flicker during any of this.** Laptop
  sleep/wake → reconnects without a manual refresh.
- **P5:** Every wrapped action: Cancel → no network request (check dev tools);
  confirm → request identical to before. Hard-delete a test cohort → preview
  count matches the server's `players_removed`. Type the wrong phrase → button
  stays locked. Freeze with a long message → players see the **full** banner;
  Unfreeze now also asks first. Log in as base facilitator → quick-bar Undo is
  disabled with a role tooltip, and force-navigating to a hidden tab shows the
  "not available" panel.

---

## Known notes / caveats

1. **EOL normalization:** the 7 pre-existing edited files were CRLF (or mixed)
   and are now committed as LF. Working tree and index agree, so `git status`
   stays clean; JS tooling is EOL-agnostic. If you prefer CRLF, add a
   `.gitattributes` rule and renormalize once.
2. The **sandbox file-sync quirk** from your last session resurfaced (mount
   truncates freshly host-written files). All phase content was therefore
   written through the VM side, syntax-checked with esbuild (JSX parse) per
   file per phase, and verified against a reconstruction from the Phase-0
   blobs — every replacement matched exactly once (or exactly twice where two
   identical handlers were deduplicated).
3. `next build` was not run in the sandbox (Turbopack + memory limits). Run
   `npm run build` (or dev) once before the next session; esbuild parse checks
   passed on every file, so surprises should be limited to lint-level issues.
4. Phase 6 (optional polish: quiz/interview panel relocation + per-cohort read,
   shortcut sheet, "Factory Nuke" copy, dead-state cleanup) was intentionally
   not implemented, per "all 5 phases".
