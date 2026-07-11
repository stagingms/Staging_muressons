# UX v3 — Phase Implementation Notes & Test Evidence

Branch: `ux/v3-phases`. Baseline: `UX_V3_S0_BASELINE.md` (pytest 976 green,
player smoke incl. the expected R2-commit 429, endpoint contract of 303 call
sites, shockwave/bell/rehearsal payload capture).

| Commit | Phase | Contents |
|---|---|---|
| `ec908f9` | S0 | v3 review document |
| `435fa52` | S0 | Baseline evidence + endpoint contract |
| *(this)* | S1 | Chrome truth & routing hygiene — G-2, G-4, F-5, F-8, F-9, G-5 |

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
