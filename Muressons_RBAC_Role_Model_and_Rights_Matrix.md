# Muressons — Role Model & RBAC Reference

**Status:** current (reflects the implemented state after the C1–C7 RBAC remediation).
**Authoritative source of truth:** `backend/admin_shared.py::ROLE_HIERARCHY` (levels) and the
`require_*` dependencies in `backend/admin_router.py` (enforcement). The frontend mirror in
`frontend/app/config/sidebarConfig.js` is pinned equal to the backend by the drift tripwire
`backend/tests/test_role_hierarchy_sync.py`.

This document is a reference. When you change a role, level, or guard, update this file **and**
the code **and** the tripwire in the same commit.

---

## 1. Model at a glance

The platform has **one linear facilitator/admin ladder** plus **one separate player realm**.

- **Facilitator/admin realm** — six role strings on five numeric levels, resolved from a signed JWT
  cookie. Authorization is a mix of *level-based* guards (rank comparison) and *name-based* guards
  (explicit role membership).
- **Player realm** — not in `ROLE_HIERARCHY` at all. Players authenticate with a Player ID (+ optional
  password) and are bound to their session by the SEC-3 ownership check (`X-Player-Id` header). A
  facilitator is never a "player" and a player is never a facilitator role.

Three of the admin identities are **virtual** — they are *not* stored in the facilitator registry and
are granted only from a signed token / environment password: `god_mode`, the master `facilitator`
login, and `project_admin`.

---

## 2. Role catalog

| Role | Level | Nature | Authenticated via | Scope | Assignable to a registry user? |
|---|---|---|---|---|---|
| `god_mode` | **4** | Virtual break-glass identity | `MASTER_PASSWORD` (login id `god_mode`) | Global — everything | **Never** |
| `super_admin` | **3** | Registry role | Registry password (JWT cookie) | Global | Yes (by super_admin/god_mode) |
| `admin` | **3** | Alias of `super_admin` | Registry password | Global | Yes |
| `lead_facilitator` | **2** | Registry role (also a virtual master `facilitator` login) | Registry password, or `MASTER_PASSWORD` with id `facilitator` | Own + assigned sessions | Yes |
| `facilitator` | **1** | Registry role | Registry password | Own sessions | Yes |
| `project_admin` | **0** | Virtual provisioning-only role | `PROJECT_ADMIN_PASSWORD` (login id `project_admin`) | Registry + cohort provisioning; **never** live runs | Yes (create only; see §7) |
| *Player* | — | Separate authz realm | Player ID (+ password) | A single session | — (not a facilitator role) |

**Role notes**

- **`god_mode` (4).** The top tier and a *distinct role string*, not an alias of super_admin. Because
  `4 > 3` it clears every level-gated super-admin check automatically. All *name-based* admin checks
  use the `is_admin_role()` helper (level ≥ super_admin) so god_mode is admitted everywhere super_admin
  is. It has a JWT-version kill-switch (`bump_token_version("god_mode")`) and a normal token TTL — no
  more immortal cookie. It is **never** assignable to a registry facilitator.
- **`super_admin` (3).** Full platform admin — global engine/config, the facilitator registry, the
  danger zone, and (by level) everything lead/facilitator/run can do.
- **`admin` (3).** A kept alias of `super_admin` so the level is never undefined. Same authority.
- **`lead_facilitator` (2).** A facilitator plus the privileged live-run interventions: manual KPI
  overrides, black-swan injection, undo round, auto-pause, per-cohort materiality.
- **`facilitator` (1).** The base simulation operator. Runs its **own** sessions (multi-tenancy via
  `owns_session`), manages its players, fires standard interventions.
- **`project_admin` (0).** A provisioning role, deliberately **off the run ladder**. It creates
  facilitators and cohorts and configures cohorts at creation, but can never operate a live run. Level
  0 (strictly below facilitator) is what makes `has_role_level(project_admin, "facilitator")` false and
  guarantees it can never satisfy `require_lead_facilitator`.
- **Player.** Authenticated and authorized entirely outside `ROLE_HIERARCHY` — see §8.

---

## 3. The level ladder & ordering invariants

```
god_mode          4   ← distinct top tier (virtual break-glass)
super_admin       3
admin             3   ← alias of super_admin
lead_facilitator  2
facilitator       1
project_admin     0   ← off the run ladder (virtual, provisioning-only)
(unknown/anon)    0   ← default for any unrecognised role
```

Invariants the guards rely on (asserted by `test_role_hierarchy_sync.py`):

- `god_mode > super_admin` — god_mode outranks super_admin.
- `super_admin == admin` — admin is an alias.
- `super_admin > lead_facilitator > facilitator` — the run ladder is a strict order.
- `project_admin < facilitator` **and** `project_admin < lead_facilitator` — project_admin is off the
  ladder and can never satisfy a lead/super gate by level.

Because guards look levels up **by name** (`ROLE_HIERARCHY.get("super_admin", …)`), the numbers can be
rescaled without touching guard code, as long as this ordering holds and the frontend mirror matches.

---

## 4. Authorization guards

All admin endpoints hang off one of these FastAPI dependencies (`admin_router.py`). "Passes" = the
role is allowed through the guard.

| Guard | Rule | god_mode | super_admin / admin | lead | facilitator | project_admin | anon |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|
| `require_super_admin` | level ≥ super_admin(3) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `require_lead_facilitator` | level ≥ lead(2) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `require_sim_manager` | authenticated **and not** project_admin | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| `require_facilitator` | any authenticated role | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `require_registry_admin` | `is_admin_role` **or** project_admin | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |

Supporting helpers:

- **`is_admin_role(role)`** → `True` when level ≥ super_admin — i.e. `super_admin`, `admin`, `god_mode`.
  Use this for every "is this an admin?" decision instead of `role == "super_admin"` (which silently
  drops god_mode).
- **`owns_session(fac, session)`** → `True` if `is_admin_role(role)` (god_mode/super_admin bypass) or
  the session's `facilitator_id` matches. Enforced by `_assert_session_ownership` on session-scoped
  writes; god_mode short-circuits.
- **`assignable_roles_for(caller_role)`** → the set of roles a caller may grant (see §7).

---

## 5. Hierarchy & Rights Matrix

Capability groups vs. roles. **✅** = permitted (enforced in backend); **❌** = denied (backend);
god_mode always ≥ super_admin. The **Guard** column names the dependency that enforces the row.
Player is a separate realm — its only "yes" is the play row.

| # | Capability group | Guard | god_mode | super_admin | lead | facilitator | project_admin | Player |
|---|---|---|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | **Global engine/config** — god settings, macro-economics, materiality *global defaults*, archetypes, BU categories, stakeholder/pillar global, decision configs, master interventions, engine tunables, scenario presets, freeze system, global side-track permissions | `require_super_admin` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 2 | **Danger zone** — factory reset, reset all/one session, backup export/import, GDPR export, clear/orphan players | `require_super_admin` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 3 | **Registry admin — mutate** — update/delete facilitator, change role, enable/disable, reset password, cohort limit, revoke sessions, rotate master password | `require_super_admin` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 4 | **Registry admin — create** — create facilitator, bulk/CSV/Excel upload | `require_registry_admin` | ✅ | ✅ | ❌ | ❌ | ✅¹ | ❌ |
| 5 | **Lead run interventions** — manual KPI override, inject black-swan/custom event, undo round, set auto-pause, per-cohort materiality dictionary, per-cohort settings write, public-status/metadata | `require_lead_facilitator` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 6 | **Live-run management** — round pacing/unlock, practice mode; player register/induct/assign/id/password; interventions (inject message, shockwave, broadcast, finale ring-bell, situation-room bulletin); impersonate; intervention-media upload; grading (bonuses, peer-eval); notes; annotations; decade-plan; what-if replay | `require_sim_manager` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 7 | **Cohort provisioning/config** — create cohort (`/simulations/start`), bu-composition, side-tracks, cohort pacing defaults, pedagogical settings, ending-pathway, CEO-interview, industry vertical, pillar config, clone cohort, allowed-interventions | `require_facilitator`² | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 8 | **Reads / dashboards** — list facilitators/players/sessions, leaderboard, reports, analytics, complexity feed, system status/health, BRSR status, config | `require_facilitator` | ✅ | ✅ | ✅ | ✅ | ✅³ | ❌ |
| 9 | **Auth / self** — login, logout, refresh own token, change own password | `require_facilitator` / open | ✅ | ✅ | ✅ | ✅ | ✅ | ✅⁴ |
| 10 | **Cross-session data access** — read/write **any** session vs. only owned | `owns_session` | ✅ all | ✅ all | own | own | n/a⁵ | own |
| 11 | **Play the simulation** — dashboard, commit turn, submit decisions | `X-Player-Id` + SEC-3 ownership | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ own |

**Footnotes**

1. **¹ project_admin create is role-scoped** — it may create **only** `lead_facilitator` and
   `facilitator` accounts (§7). It cannot create `super_admin`, `admin`, `project_admin`, or `god_mode`.
2. **² cohort creation** — `POST /api/simulations/start` requires an authenticated facilitator and
   derives the owning `facilitator_id` from the JWT; registry admins (super_admin/god_mode/project_admin)
   may create on behalf of another facilitator, everyone else is pinned to their own id. Self-paced play
   uses the separate ungated `/solo-start`.
3. **³ project_admin reads** — the API permits project_admin to hit `require_facilitator` reads, but its
   UI exposes only two tabs (`dashboard_home`, `facilitator_registry`), so in practice it sees the
   registry and its provisioning dashboard.
4. **⁴ Player auth** — via the player login/join endpoints, not the facilitator guard chain.
5. **⁵ project_admin never operates runs**, so session ownership does not apply to it; its run access is
   denied upstream by `require_sim_manager`.

---

## 6. Tab entitlements (`ROLE_ALLOWED_TABS`)

Backend-authoritative tab lists (frontend filters against these, plus `requiredRole` on individual
items).

| Role | Tabs |
|---|---|
| `super_admin` / `god_mode` | `*` (all) |
| `lead_facilitator` | all facilitator tabs **plus** `manual_override`, `auto_pause`, `undo_round`, `materiality`, `activity_log` |
| `facilitator` | `dashboard_home`, `timeline`, `teleprompter`, `leaderboard`, `registry`, `session_viewer`, `impersonate`, `swipe_file`, `broadcast`, `platform_analytics`, `cohort_comparison`, `complexity_feed`, `decision_replay`, `debrief`, `dna_comparison`, `scorecard_evaluator`, `bonuses`, `peer_eval`, `reports`, `notes`, `annotations`, `teaching_journal`, `technical_glossary`, `intervention_config` |
| `project_admin` | **fixed, non-cumulative**: `dashboard_home`, `facilitator_registry` |

Note the distinction between *tab visibility* (UX) and *endpoint authorization* (security). Tabs are a
convenience filter; the `require_*` guards are the real enforcement. A hidden tab whose endpoint isn't
guarded is still reachable via the API — always gate the endpoint.

---

## 7. Role-assignment matrix (`assignable_roles_for`)

Role assignment is **caller-scoped** and enforced on all four write paths — `create_facilitator`,
`bulk_create_facilitators`, `update_facilitator`, `update_facilitator_role`. A caller may never grant a
role above its own tier, and `god_mode` is excluded from the assignable set for everyone.

| Caller role | May grant | May NOT grant |
|---|---|---|
| `god_mode` (4) | super_admin, admin, lead_facilitator, facilitator, project_admin | **god_mode** |
| `super_admin` / `admin` (3) | super_admin, admin, lead_facilitator, facilitator, project_admin | god_mode |
| `project_admin` (0) | **lead_facilitator, facilitator only** | super_admin, admin, project_admin, god_mode |
| `lead_facilitator` / `facilitator` | — (not registry admins; role change is super-admin-only) | anything |

`_ASSIGNABLE_ROLES = {super_admin, admin, lead_facilitator, facilitator, project_admin}` — the virtual
`god_mode` tier is intentionally absent, so it can never be created or set through the registry API.

---

## 8. Player authorization realm (separate)

Players live entirely outside `ROLE_HIERARCHY`.

- **Authentication:** `POST /api/simulations/player-login` (Player ID + password; cohort auto-resolved),
  or `POST /api/simulations/public/sessions/{id}/join`.
- **Authorization / multi-tenancy (SEC-3):** session-scoped player routes (`get_dashboard`,
  `commit_turn`, decision submission) validate the `X-Player-Id` header against the session's owner.
  Wrong owner → `403 "not the owner of this session"`. No header → backward-compatible bearer behaviour
  (also how facilitator/observer clients read these routes).
- **Player unlock (P6):** support access to a player account uses `PLAYER_MASTER_PASSWORD` — a secret
  **separate** from the admin `MASTER_PASSWORD` — and is **disabled by default**.
- A facilitator role can never act as a player and vice-versa; reasoning about "who can do what"
  requires holding both models at once.

---

## 9. Break-glass secrets

| Secret (env) | Unlocks | Realm | Default | Notes |
|---|---|---|---|---|
| `MASTER_PASSWORD` | `god_mode` login + master-bypass of any **facilitator** login + role-change re-verify | Admin | `sim2026@iim` (dev) | Audit-logged (`master_password_bypass`). **Does not** unlock players (P6). Set `""` to disable. |
| `PLAYER_MASTER_PASSWORD` | Any **player** account | Player | *empty → disabled* | P6: separate from the admin secret; no fallback. Use a value distinct from `MASTER_PASSWORD`. |
| `PROJECT_ADMIN_PASSWORD` | The virtual `project_admin` account | Admin (provisioning) | `simadmin2026@` (dev) | Grants provisioning-only authority. |

The god_mode token carries a monotonic `ver` claim; `bump_token_version("god_mode")` invalidates every
outstanding god_mode cookie on the next request (the revocation kill-switch).

---

## 10. Conventions & drift protection

When touching auth, follow these (also recorded in `CLAUDE.md`):

1. **Use the level, not the string.** For any "is this an admin?" decision use `is_admin_role(role)`,
   never `role == "super_admin"` — the latter silently drops god_mode. Level-gated guards
   (`require_super_admin`, `require_lead_facilitator`) already pass god_mode because `4 > 3 > 2`.
2. **Run management gates on `require_sim_manager`, not `require_facilitator`.** `require_facilitator`
   admits project_admin; `require_sim_manager` excludes it. Every endpoint that operates a *live run*
   must use `require_sim_manager`. Cohort *provisioning/config* endpoints stay on `require_facilitator`
   because project_admin performs them while provisioning.
3. **Role assignment is caller-scoped** via `assignable_roles_for(caller_role)` on all four write paths.
4. **One ladder, mirrored, pinned.** `ROLE_HIERARCHY` is defined in `admin_shared.py` and mirrored in
   `sidebarConfig.js`; `test_role_hierarchy_sync.py` fails the build on any drift. Change both in the
   same commit.

**Regression coverage:** `test_role_hierarchy_sync.py` (ladder/mirror), `test_p1_role_assignment_scope.py`
(caller-scoped grants), `test_c3_project_admin_run_isolation.py` (run isolation + refresh),
`test_p6_master_secret_separation.py` (secret separation), `test_security_guards.py` (unauthenticated
rejection incl. cohort creation), `test_sec3_session_ownership.py` (player ownership).

---

*Reference generated from the implemented code on 2026-07-12. Pair with
`REVIEW_Muressons_RBAC_RoleHierarchy_Audit_v1.md` (the audit + fix history) and the `CLAUDE.md`
"Role model & RBAC" section (the short convention summary).*
