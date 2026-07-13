# Muressons — Role Hierarchy, Rights & Conflict Audit (v1)

**Scope:** `god_mode`, Super Admin, Lead (Facilitator), Facilitator, Project Admin, Player.
**Method:** evidence-based, read-only. Every claim cites file + symbol. Rights are graded
**[BE]** enforced in backend, **[FE]** frontend-only (display/UX), or **[—]** absent.
**Date:** 2026-07-12.

> **⚠️ Implementation status (update, 2026-07-12).** Sections 0–1 below describe the model **as
> originally found**. All conflicts C1–C7 have since been **fixed in code** (see the ✅ markers in
> §2 and §3). The role ladder is now: **god_mode = 4** (distinct tier) · super_admin / admin = 3 ·
> lead_facilitator = 2 · facilitator = 1 · **project_admin = 0** (off the run ladder) · Player =
> separate realm. Read §0–§1 as the *before* picture; the resolution notes are the *current* state.

---

## 0. What the code actually models (vs. the requested six-tier list)

The requested hierarchy implies six ranked tiers. The code does **not** model six ranks.
It defines **four role strings on three numeric levels**, plus two things that sit *outside*
that ladder:

`backend/admin_shared.py:30` — `ROLE_HIERARCHY`:

```
super_admin = 3   (alias "admin" = 3)
lead_facilitator = 2
facilitator = 1
project_admin = 1        # same level as facilitator, disjoint powers
```

- **`god_mode` is not a distinct tier.** It is a *virtual identity* that resolves to
  `super_admin`. Login maps it there (`admin_router.py:1753`), and privilege resolution
  returns `"super_admin"` for it (`admin_router.py:207`). god_mode ≡ super_admin in authority;
  the only differences are (a) it lives outside the registry and (b) it authenticates via the
  master password. Treating it as "above" super_admin is a documentation artifact, not code.
- **`Player` is not in the RBAC model at all.** Players authenticate through a *separate*
  system: `router.py:288 player_login`, an `X-Player-Id` header, and the SEC-3 session-ownership
  gate (`backend/tests/test_sec3_session_ownership.py`). `has_role_level()` cannot reason about
  players.
- Two more virtual master accounts exist that the request didn't name: a master **`facilitator`**
  account → `lead_facilitator` (`admin_router.py:1762`), and the `"admin"` alias → `super_admin`.

So the real picture is **three tiers + one off-ladder peer (project_admin) + a separate Player realm**,
reached by **three login identities that are virtual** (god_mode, facilitator, project_admin).

---

## 1. Hierarchy & Rights Matrix

Authentication and privilege resolution: `get_fac_role()` (`admin_router.py:183`) trusts **only**
the signed JWT cookie; the `X-Facilitator-Id` header path was removed (`auth_jwt.py:209`). Registry
is re-checked every request so demotion/disable is immediate (`admin_router.py:218`, H-4).

| Capability (guard) | god_mode | Super Admin | Lead | Facilitator | Project Admin | Player |
|---|---|---|---|---|---|---|
| Hierarchy level | 3 (virtual) | 3 | 2 | 1 | 1 (disjoint) | n/a |
| Granted / revoked by | Master password (`master_credentials.py`) | god_mode via role change | Super Admin | Registry admin | `PROJECT_ADMIN_PASSWORD` env | Facilitator-issued Player ID |
| Scope | Global | Global | Own + assigned sessions | Own sessions | Registry + cohort provisioning | Single session |
| Global god-mode settings (`require_super_admin`) | ✅ **[BE]** | ✅ **[BE]** | ❌ | ❌ | ❌ | ❌ |
| Change a facilitator's role (`require_super_admin` + password re-verify, `:833`) | ✅ **[BE]** | ✅ **[BE]** | ❌ | ❌ | ❌ | ❌ |
| Create / bulk-create facilitators (`require_registry_admin`, `:1319/:1595`) | ✅ **[BE]** | ✅ **[BE]** | ❌ | ❌ | ✅ **[BE]** | ❌ |
| Manual KPI override / inject event (`require_lead_facilitator`, `:4012/:4106`) | ✅ **[BE]** | ✅ **[BE]** | ✅ **[BE]** | ❌ | ❌ | ❌ |
| Set pacing / unlock round / inject message (`require_facilitator`, `:2633/:2731/:4357`) | ✅ **[BE]** | ✅ **[BE]** | ✅ **[BE]** | ✅ **[BE]** | ⚠️ **passes guard [BE]** | ❌ |
| Detonate shockwave (`require_facilitator` + capability, `:4273`) | ✅ **[BE]** | ✅ **[BE]** | ✅ **[BE]** | ✅ (if flag) **[BE]** | ❌ blocked at `:4255` **[BE]** | ❌ |
| Remove player (`require_sim_manager`, `:3142`) | ✅ **[BE]** | ✅ **[BE]** | ✅ **[BE]** | ✅ **[BE]** | ❌ blocked **[BE]** | ❌ |
| Create a cohort/session (`/api/simulations/start`, `router.py:606`) | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ **anyone — no guard** |
| Access any session's data (`owns_session`, `admin_shared.py:119`) | ✅ bypass **[BE]** | ✅ bypass **[BE]** | own only **[BE]** | own only **[BE]** | virtual → bypass **[BE]** | own session **[BE]** |
| Sidebar tab visibility (`filterSidebarForRole`) | all | all | fac+lead | fac set | fixed 2 tabs | n/a |
| Tab list — display filter only | **[FE]** | **[FE]** | **[FE]** | **[FE]** | **[FE]** | n/a |

Tab entitlements (`ROLE_ALLOWED_TABS`, `admin_shared.py:42`): facilitator = base set; lead =
base **+** `manual_override, auto_pause, undo_round, materiality, activity_log`; super_admin = `*`;
project_admin = **fixed** `{dashboard_home, facilitator_registry}` (deliberately non-cumulative,
`:99`).

---

## 2. Conflicts & Contradictions

### C1 — Privilege escalation: Project Admin can mint Super Admins **[HIGH]** — ✅ FIXED
`create_facilitator` (`:1319`) and `bulk_create_facilitators` (`:1595`) are guarded by
`require_registry_admin`, which admits `project_admin` (`:275`). The role of the new account is
taken verbatim from the request body — `role = req.role or "facilitator"` (`:1337`, model default
`:365`) — with **no check that the caller is allowed to grant that role**. A level-1 project_admin
can therefore create a `role: "super_admin"` account and log in as it.

**Intended policy:** a project admin may create **only** `lead_facilitator` and `facilitator`
accounts — no other role (not `super_admin`, `project_admin`, `admin`, or `god_mode`) is permitted.

**Resolution (implemented, = P1):** role assignment is now caller-scoped via
`assignable_roles_for(caller_role)` (`admin_shared.py`): a caller may never grant a role above its own
tier, `project_admin` may grant **only** `lead_facilitator`/`facilitator`, and `god_mode` is never
grantable by anyone (it is excluded from `_ASSIGNABLE_ROLES`). This is enforced on **all four**
role-writing paths — `create_facilitator`, `bulk_create_facilitators` (hardcodes `facilitator`),
`update_facilitator` (generic update) and `update_facilitator_role` — closing the create-side door to
match the already-hardened change-role path. Validated: project_admin → 403 on super_admin/god_mode
creation, 200 on lead/facilitator; god_mode caller → 403 assigning god_mode, 200 assigning super_admin.

### C2 — Unauthenticated cohort creation & facilitator-ID spoofing **[HIGH]** — ✅ FIXED
`POST /api/simulations/start` (`router.py:606`) previously had **no auth dependency**. `facilitator_id`
was read from the request body and fed straight into `check_and_increment_cohort_count(body.facilitator_id)`.
Consequences: (a) any unauthenticated caller could create cohorts; (b) an attacker could spoof any
`facilitator_id` and burn a victim's cohort quota, or pass a bogus ID to dodge limits entirely.

**Resolution (implemented):** `start_simulation` now resolves the caller from the signed JWT
(`get_facilitator_from_request` / `get_fac_role`) and rejects anonymous callers with 401. The owning
`facilitator_id` is taken from the verified identity, not the raw body: registry-level admins
(super_admin / god_mode / project_admin) may still create a cohort on behalf of another facilitator
(the FacilitatorManager "seed alpha cohort" flow), but any other role is pinned to its own id and a
body value naming a *different* facilitator is rejected with 403. Self-paced play is unaffected — it
uses the dedicated ungated `/solo-start`. See `router.py:606-654`.

**Validation:** direct behavioural check (anonymous → 401, spoofed id → 401, authenticated → 201,
downstream player-join intact) passes 5/5, and the SEC-3 ownership suite + MP-commit suite pass 8/8
with the auth-aware fixtures. New regression tests added in `test_security_guards.py`
(`test_start_simulation_requires_auth`, `test_start_simulation_spoofed_facilitator_id_rejected`).

### C3 — "Project Admin never manages runs" is asserted but under-enforced **[MEDIUM]** — ✅ FIXED
The design intent is explicit: *"Registry admin: provisions facilitators + cohorts, NEVER manages
runs"* (`admin_shared.py:35`). Enforcement relied on `require_sim_manager`, which excludes
project_admin (`:282`). But `require_sim_manager` previously guarded **exactly one** endpoint
(`remove_player`, `:3142`), whereas **74 endpoints** used `require_facilitator`, which admits
project_admin. So project_admin *passed the guard* on run-management actions such as `set_pacing`,
`unlock_next_round` and `inject_message`.

**Resolution (implemented):** the 28 live-run-management endpoints were moved from
`require_facilitator` to `require_sim_manager`, which now guards the whole run-operation surface —
round pacing/unlock and practice mode; player registration, induction, assignment, id generation and
credential resets; the team decade-plan; live interventions (inject message, shockwave, broadcast,
finale ring-bell, situation-room bulletin); impersonation and intervention-media upload; grading
(bonuses, peer-eval deletion); and notes/annotations/cohort-pulse. `require_sim_manager` admits every
real facilitator tier (base / lead / super / god_mode) and rejects **only** project_admin (and
anonymous), so no facilitator flow changes — only project_admin loses run access. The boundary is
deliberate: cohort **provisioning/config** endpoints that project_admin uses while creating a cohort
(bu-composition, side-tracks, cohort pacing defaults, pedagogical settings, ending-pathway,
CEO-interview) stay on `require_facilitator`, as do reads and `/auth/refresh`. See the expanded
`require_sim_manager` docstring (`admin_router.py:282`).

**Validation:** `test_c3_project_admin_run_isolation.py` — project_admin gets 403 on run endpoints,
stays allowed on provisioning + reads, and a lead facilitator is never caught by the project-admin
gate. Full guard/ownership/multiplayer suites pass 24/24 with the change.

*Related fix — project_admin session refresh: `/auth/refresh` (`:1911`) had a god_mode special-case
but no project_admin one, so the virtual project_admin account 401'd on the registry lookup and could
never refresh its JWT (forcing a re-login on expiry). A matching project_admin branch was added
(mirrors god_mode: re-issues the token, returns role + fixed tabs). The refreshed session remains
blocked from run management. Covered by `test_project_admin_can_refresh_session`.*

### C4 — Hierarchy inversion: two roles at level 1 with each-exclusive rights **[MEDIUM]** — ✅ FIXED
`project_admin` and `facilitator` were both level 1 but their powers are **disjoint, not nested**:
project_admin can hit the registry (`require_registry_admin`) which base facilitator cannot; base
facilitator can manage runs (`require_sim_manager`) which project_admin cannot. Yet `has_role_level()`
uses a total order (`>=`), so `has_role_level(project_admin, "facilitator")` returned `True` — the code
asserted project_admin ⊇ facilitator, which is false.

**Resolution (implemented):** project_admin was moved to **level 0** — off the run ladder entirely,
strictly below facilitator(1) and lead(2). `has_role_level(project_admin, "facilitator")` is now
`False`, removing the inversion, and project_admin can never satisfy `require_lead_facilitator`. Its
provisioning powers remain name-gated (`require_registry_admin`) and its run exclusion is enforced by
`require_sim_manager` (C3), so the level change strips no legitimate power. All level-based guards use
name lookups, so nothing else shifted. Mirrored in the frontend and pinned by the C5 tripwire.
(The deeper capability-model refactor — replacing the single linear rank with per-role capability
allow-sets — remains an optional future improvement, but the inversion itself is resolved.)

### C5 — Dual source of truth for the role ladder, no drift guard **[MEDIUM]** — ✅ FIXED
`ROLE_HIERARCHY` is defined twice: backend `admin_shared.py` and frontend `sidebarConfig.js`, with a
self-aware comment: *"There is currently no automated check — a drift will silently break tab
filtering."*

**Resolution (implemented):** added `backend/tests/test_role_hierarchy_sync.py` — it parses the
frontend `sidebarConfig.js` `ROLE_HIERARCHY` and asserts an exact match with the backend dict, plus
ordering invariants (god_mode > super_admin > lead > facilitator > project_admin; project_admin below
lead). Both files now carry a SYNC-WARNING header pointing at the tripwire. Same failure class the repo
already gates for the shockwave catalog; the guard now exists here too. Passing 2/2.

### C6 — god_mode / super_admin / "admin" conflation **[LOW / conceptual]** — ✅ FIXED
Three names — `god_mode`, `super_admin`, `admin` — all resolved to level 3 with identical authority,
and get_fac_role returned `"super_admin"` for the god_mode account, so god_mode was indistinguishable
as a tier.

**Resolution (implemented):** god_mode is now a **distinct level-4 role**. `ROLE_HIERARCHY["god_mode"]
= 4`; login/refresh/`get_fac_role` resolve the god_mode account to the `"god_mode"` role string (older
cookies carrying `"super_admin"` still resolve, for a clean transition). Because 4 > 3, god_mode clears
every level-gated super-admin check automatically; the **name-based** checks that gated admin power
(is_admin flag, all-tabs, session-ownership bypass, `require_registry_admin`, role-change re-verify,
password-change and note-delete authority, the router.py cohort registry-admin set, and the stale
duplicate resolver in `admin_analytics.py` — now de-duplicated to delegate to the canonical
`get_fac_role`) were switched to the level-based `is_admin_role(role)` helper so god_mode retains full
super authority. `admin` remains an explicit
alias of `super_admin` (level 3). god_mode is **not assignable** to a registry facilitator (blocked in
create/update/role endpoints — see P1). Validated 18/18 (login → role `god_mode`, is_admin, all-tabs,
passes require_super_admin, refresh preserved) and reconciled in `CLAUDE.md`.

### C7 — One master secret crosses every boundary, including Player **[LOW]** — ✅ FIXED
`verify_master_password()` was the bypass for god_mode login, facilitator master-login, role-change
re-verification, **and** player unlock (`router.py:339, 437`) — a single secret spanning the admin
*and* player realms, so one leak had total blast radius.

**Resolution (implemented, = P6):** the player realm now has its own secret, `PLAYER_MASTER_PASSWORD`
(`config.py`), checked by `verify_player_master_password()` (`master_credentials.py`). Player login
(`router.py:339, 437`) uses it instead of the admin `MASTER_PASSWORD`, so the admin break-glass secret
can no longer unlock player accounts. It is **disabled by default** (empty) with no fallback to the
admin secret, and documented in `.env.example`. Validated: admin master verifies for the admin realm
but returns False for player unlock; when a distinct `PLAYER_MASTER_PASSWORD` is set it unlocks players
and the admin secret still does not. Covered by `test_p6_master_secret_separation.py`.

### C8 — Player lives in a parallel authz system **[LOW / informational]**
Players are authorized entirely outside `ROLE_HIERARCHY` (separate login, `X-Player-Id`, SEC-3
ownership). Reasoning about "who can do what" therefore requires holding **two** models at once. Fine
architecturally; a hazard for anyone assuming a single RBAC lattice.

---

## 3. Resolution Plan (ordered by severity)

**P1 — Close the create-facilitator escalation (fixes C1). ✅ DONE.** Added
`assignable_roles_for(caller_role)` (`admin_shared.py`) and enforced it on all four role-writing paths
(`create_facilitator`, `bulk_create_facilitators`, `update_facilitator`, `update_facilitator_role`):
project_admin may grant only lead/facilitator; nobody may grant god_mode; no caller may grant above its
own tier. Regression coverage in `test_role_assignment_scope`/the C4-C6 validation.

**P2 — Authenticate cohort creation (fixes C2). ✅ DONE.** `start_simulation` now requires an
authenticated facilitator and derives the owning `facilitator_id` from the verified JWT identity
rather than the request body; a non-admin naming a different facilitator is rejected. The public/solo
path remains on the dedicated ungated `solo_start` endpoint (`router.py:746`). Implemented at
`router.py:606-654`; fixtures in `test_sec3_session_ownership.py`, `test_mp_commit_indicator.py`,
`test_systemic_risk_integration.py` updated to authenticate, and guard regression tests added to
`test_security_guards.py`.

**P3 — Enforce "project_admin never manages runs" structurally (fixes C3). ✅ DONE (tactical pass).**
The 28 run/manage routes tagged `require_facilitator` were switched to `require_sim_manager`
(`set_pacing`, `unlock_next_round`, `inject_message`, player management, live consoles, grading,
notes/annotations, and peers), which excludes project_admin while admitting every facilitator tier.
Cohort provisioning/config routes were intentionally left on `require_facilitator`. Regression tests
in `test_c3_project_admin_run_isolation.py`; 24/24 across the guard/ownership/multiplayer suites.
The deeper capability-model refactor for C4 (replacing the total-ordered level with an explicit
allow-list so same-level disjoint roles stop colliding) remains a recommended follow-up.

**P4 — Add a role-ladder drift tripwire (fixes C5). ✅ DONE.** Added
`backend/tests/test_role_hierarchy_sync.py` — parses the frontend `sidebarConfig.js` `ROLE_HIERARCHY`
and asserts exact equality with the backend dict, plus ordering invariants. Both files carry a
SYNC-WARNING header. (Implemented as a pytest tripwire rather than jest so it runs in the backend
suite; a jest variant could be added later to also gate frontend-only CI.)

**P5 — Reconcile the model in docs (fixes C6 + C8). ✅ DONE.** Added a "Role model & RBAC" section to
`CLAUDE.md`: the full role/level table (god_mode 4 · super_admin/admin 3 · lead 2 · facilitator 1 ·
project_admin 0 · Player = separate realm), plus the three standing conventions — use `is_admin_role`
not `== "super_admin"`; run management gates on `require_sim_manager`; role assignment is caller-scoped
via `assignable_roles_for`. (Reworded from the original "god_mode is an alias" framing to match the C6
decision that god_mode is a distinct tier.)

**P6 — Split the master secret across realms (addresses C7). ✅ DONE.** Added `PLAYER_MASTER_PASSWORD`
(`config.py`) + `verify_player_master_password()` (`master_credentials.py`); player login now uses it,
so the admin `MASTER_PASSWORD` no longer unlocks players. Disabled by default, no fallback, documented
in `.env.example`. Tests in `test_p6_master_secret_separation.py`.

**Status:** P1 ✅ · P2 ✅ · P3 ✅ (tactical pass; capability-model refactor optional) · P4 ✅ · P5 ✅ ·
P6 ✅. All C1–C7 findings are resolved in code; C8 (Player as a separate authz realm) is now documented
in `CLAUDE.md` rather than "fixed" — it is a correct architectural fact, not a defect.

---

*Read-only analysis; no code was modified. Every cited line was read directly from the working tree
on 2026-07-12.*
