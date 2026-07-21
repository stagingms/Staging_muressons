# Audit — role guards & in-memory store reads (2026-07-18)

Trigger: three facilitator-dashboard breakages shared one pattern family
(undo-round NameError, decision-history stuck at R1, Cohort Analytics 403).
This sweep AST-parsed all 319 routed endpoints in `admin_router.py`,
`admin_analytics.py`, `admin_resources.py`, `admin_teleprompter.py`,
`router.py`, mapped each to its guard + data sources, and cross-referenced
the ~120 API calls reachable from the facilitator dashboard's component tree.

## Fixed in this pass

1. **CreateCohortModal → PATCH /global-settings from the CEO-interview
   controls.** The wizard's ENABLED toggle and voice select PATCHed GLOBAL
   settings on every click: silent 403 for facilitators (swallowed by
   `catch {}` while the UI toggled optimistically), and for admins a global
   mutation as a side effect of poking a *cohort* wizard. Removed — state is
   local until the wizard's per-cohort save step
   (`PUT /sessions/{sid}/ceo-interview`), which was already the source of
   truth.
2. **PlayerRegistry "Clear All Orphans"** rendered for every facilitator but
   `DELETE /players/orphans` is super_admin — silent 403. Now behind
   `isSuperAdmin`.

## Previously fixed, same family

- undo-round: bare `_global_states` NameError (bc9775b)
- decision-history: read empty memory store under DB backend (1d999e0)
- /god/analytics: super_admin guard 403'd the facilitator tab; now
  facilitator-scoped (4c7ef62)

## Clean

- **No undefined store names remain** (AST check: every `_sessions` /
  `_global_states` / `_bu_states` / `_decision_log` load is either a
  function-local `from database_memory import …` or `getattr(db, …)`).
- All other super_admin-guarded routes called from facilitator-reachable
  components are in admin-gated UI by design (FacilitatorManager registry
  actions, MaterialityConfig editor — super-admin-only per CLAUDE.md,
  SimulationSwitchboard, per-fac visibility editor) or are unguarded GETs
  misflagged by method-blind matching.

## Known debt — NOT fixed here (needs a decision)

### A. `getattr(db, '_store', …)` reads — work in memory mode, EMPTY under Postgres
The deployment currently runs memory mode (`main.py` aliases
`sys.modules["database"] = database_memory`), so these work today. If the
platform ever switches to the Postgres backend (`database.py`), each returns
`{}`/`[]` and its feature silently blanks. Port to `db.fetch_*` (as done for
decision-history) before any Postgres migration:

| Endpoint | Guard |
|---|---|
| POST /{cohort_id}/situation-room/bulletin | sim_manager |
| GET /complexity-events/{session_id} | **none** |
| GET /complexity-events-all | facilitator |
| GET /session-health | facilitator |
| POST /sessions/{session_id}/clone | facilitator |
| GET /cross-paradigm-comparison | facilitator |
| GET /cohort-comparison | facilitator |
| GET /cohort-pulse/{cohort_id} | **none** |
| GET /god/analytics | facilitator (scoped) |
| GET /analytics/player/{session_id} | **none** |

### B. Unguarded data GETs (anonymous-readable)
Most unguarded GETs are harmless config/catalog reads. Three returned
session/team data:
- `GET /cohort-pulse/{cohort_id}` — **FIXED**: facilitators (any
  authenticated role) always pass; player callers admitted only when the
  cohort's `cohort_pulse_player_visible` flag is on AND their X-Player-Id
  owns a session in the cohort. Verified all five paths live (anonymous
  401/403, facilitator 200, member player 200 when visible, non-member 403).
- `GET /complexity-events/{session_id}` — **FIXED**: require_facilitator.
  Its only consumers are the facilitator and god-mode dashboards
  (ComplexityEventFeed); the sibling /complexity-events-all was already
  facilitator-guarded.
- `GET /analytics/player/{session_id}` — **FIXED**: player-facing
  (PlayerAnalytics in the player cockpit), so it gets SEC-3 semantics
  mirroring router._assert_player_owns_session: facilitators always pass;
  an OWNED session admits only its X-Player-Id owner (leaked session ids
  alone are rejected); an unowned solo session keeps its UUID-as-bearer
  behaviour. PlayerAnalytics.js now sends the playerIdHeader (exported from
  useSimulation). Verified all paths live.

**Section B is now fully closed.** Remaining debt is Section A only (the
Postgres-migration porting checklist).
