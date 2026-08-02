# Muressons RBAC Audit — Roles, Authorities, and the Three Provisioning Flows

**Date:** 2026-08-01 · **Scope:** god_mode, super_admin, lead_facilitator, facilitator, project_admin — as they affect **cohort formation**, **facilitator creation**, and **player-ID generation**.
**Method:** every claim below is grounded in the source at a cited file:line and, where behavioural, confirmed by grep/enumeration. Nothing here is inferred from documentation alone.

---

## 1. The role ladder as it actually is (verified)

`ROLE_HIERARCHY` in `backend/admin_shared.py:30` is the single authoritative ladder, mirrored to `frontend/app/config/sidebarConfig.js` and pinned equal by `test_role_hierarchy_sync.py` (passing).

| Role | Level | Authenticated via | Intended charter |
|---|---|---|---|
| `god_mode` | 4 | signed master-password token (virtual) | break-glass; clears every level gate automatically; never assignable |
| `super_admin` / `admin` | 3 | registry password (or master pw) | full platform admin; `admin` is a level-3 alias |
| `lead_facilitator` | 2 | registry password | facilitator + overrides / undo / auto-pause |
| `facilitator` | 1 | registry password | base run operator |
| `project_admin` | 0 | `PROJECT_ADMIN_PASSWORD` env (virtual) | provisioning-only; **off** the run ladder |

This ladder itself is coherent: `god_mode ≥ super_admin` by level, so level-gated guards admit god_mode automatically, and `assignable_roles_for` (`admin_shared.py:59`) correctly prevents anyone from granting `god_mode` and caps `project_admin` at `lead_facilitator`. **The problems are not in the ladder — they are in how three parallel authorization systems disagree about the same capability.**

## 2. The three authorization systems in play

The codebase gates the same actions through **three independent mechanisms** that were meant to agree and no longer do:

1. **Route guards** (`require_super_admin`, `require_lead_facilitator`, `require_sim_manager`, `require_registry_admin`) — level- or name-based, on the API. *These are the real enforcement.*
2. **Sidebar tabs** with `requiredRole` (`sidebarConfig.js`) — role-based, in the UI.
3. **The per-facilitator `permissions` dict** (`can_create_cohorts`, `can_undo_rounds`, …) — authored at creation, editable in the Registry, returned at login. *This one enforces nothing.*

---

## 3. Findings

### F1 — HIGH · The per-facilitator `permissions` dict is entirely inert

Every facilitator record carries a `permissions` object set at creation (`admin_router.py:1830`, `:2146`) — `can_create_cohorts`, `can_undo_rounds`, `can_override_decisions`, `can_modify_materiality`, `can_manage_auto_pause`, `can_enable_side_tracks`. It is editable in the Registry UI and returned in the login response.

**It is never read for any authorization decision.** A grep for enforcement reads of each key returns **zero** across the entire backend; the only `can_*` helpers that exist (`can_orchestrate_turnaround`, `can_access_tab`) are role/tab based and never consult this dict. Actual capability gating is done entirely by role — e.g. the Undo Round tab is `requiredRole: 'lead_facilitator'` (`sidebarConfig.js:156`), not by `can_undo_rounds`.

**Adverse impact.** A super_admin who unticks "can undo rounds" (or any capability) for a lead facilitator sees the change save and persist — and it does **nothing**. The lead facilitator retains the capability because it is granted by their *role*, not the flag. This is the most dangerous kind of RBAC defect: an authority control that looks authoritative and silently isn't. It directly misleads anyone administering facilitator permissions.

### F2 — MEDIUM · "Can create a cohort" has three different answers

The single capability *create a cohort* is decided three incompatible ways:

| Surface | Rule | Evidence |
|---|---|---|
| Dashboard-home button | `permissions.can_create_cohorts !== false` (role fallback if absent) | `facilitator/page.js:920` |
| Registry-tab "+ New Cohort" button | `role !== 'facilitator'` (ignores the permission) | `facilitator/page.js:1003` |
| Backend `POST /api/simulations/start` | **any authenticated facilitator** + quota (ignores both) | `router.py:987`, `:1012` |

The `/start` route has **no role `Depends` guard** — it only rejects anonymous callers and enforces the cohort quota (`check_and_increment_cohort_count`, `admin_shared.py:1552`), which itself never consults `can_create_cohorts`.

**Adverse impact.** A base `facilitator` whose profile says `can_create_cohorts: false` and who is denied the button in both UI surfaces **can still create a cohort by calling the API directly**. The two UI surfaces also disagree with *each other*. For an audit of "who can form cohorts," the honest answer today is "any logged-in facilitator with quota remaining," which contradicts both the permission model and the intended `facilitator = own sessions` charter.

### F3 — MEDIUM · The facilitator-list endpoint drops the `admin` alias and keys god_mode by id

`GET /api/admin/facilitators` decides who may see all records with:

```python
is_admin_caller = (caller_role == "super_admin") or (caller_id == "god_mode") or (caller_role == "project_admin")   # admin_router.py:1782
```

This is the exact anti-pattern the repo's own conventions forbid ("use `is_admin_role(role)`, never `role == 'super_admin'` — the latter silently drops god_mode"). Two concrete defects:

- A facilitator whose role is the **documented alias `admin`** (level 3, super-admin-equivalent everywhere else) fails `== "super_admin"` and is treated as non-admin — they would see only their own record.
- god_mode is admitted by **id** (`caller_id == "god_mode"`), not role. It works only because that identity's id happens to be the literal string; it is fragile and inconsistent with every level-gated guard.

**Adverse impact.** Inconsistent admin classification on a PII-listing endpoint. Low security blast radius, but it is a live correctness bug and a violation of the codebase's stated rule.

### F4 — LOW/MEDIUM · Two facilitator-creation endpoints, divergent authorization

| Endpoint | Guard | project_admin? |
|---|---|---|
| `POST /facilitators` | `require_registry_admin` | ✅ yes |
| `POST /facilitators/bulk` | `require_registry_admin` | ✅ yes |
| `POST /facilitators/bulk-upload` | `require_registry_admin` | ✅ yes |
| `POST /facilitators/batch` | `require_super_admin` | ❌ **no** |

`/facilitators/batch` (`admin_router.py:2360`) is stricter than its three siblings and is **not called by the frontend** (grep of `frontend/` for `facilitators/batch` returns nothing). So `project_admin` can batch-create facilitators via `/bulk` but is 403'd on `/batch`, and there is a dead, more-restrictive duplicate creation path.

**Adverse impact.** A maintenance and reasoning hazard: a future change made to one batch path silently doesn't apply to the other, and the authz story for "who can bulk-create facilitators" has two answers.

### F5 — LOW · project_admin model tensions (documentation/consistency)

- **(a) Grants above its own level.** `project_admin` is level 0 (below `facilitator`), yet `assignable_roles_for("project_admin")` returns `{lead_facilitator, facilitator}` (`admin_shared.py:64`) — it can create accounts *two levels above itself*. This is a deliberate, documented exception, but it contradicts the general rule stated three lines above it ("a caller may never grant a role above its own tier"). Level 0 invites the misreading "least privileged," when project_admin is in fact a powerful provisioning identity.
- **(b) "Virtual" but also assignable.** The role is documented as "Virtual (env-password)", yet `_ASSIGNABLE_ROLES` (`admin_shared.py:56`) includes `"project_admin"`, so a super_admin can mint a **registry** facilitator with `role: project_admin`. Two kinds of project_admin can therefore exist; the "virtual-only" description is imprecise.

**Adverse impact.** No security hole, but the mental model is genuinely confusing — exactly the "confusing role assignment" the audit was asked to surface.

### F6 — LOW · project_admin can create a cohort but cannot populate it

`POST /start` admits `project_admin` (it is in `_REGISTRY_ADMIN_ROLES`, `router.py:1018`), so project_admin can create a cohort — even under another facilitator's id. But **every player-ID mint is `require_sim_manager`** (`generate-player`, `players/register`, `players/induct`, resets — all at `admin_router.py:3843,3865,4223,4493`), which explicitly excludes `project_admin` (`admin_router.py:191`).

So project_admin provisions the cohort **shell** and then cannot generate a single player id for it — the owning facilitator must. This is defensible under "provisions cohorts, never manages runs," and player generation is legitimately run-management. But the seam is unstated and surprising: "provision a cohort" does not include "provision its roster."

**Adverse impact.** Workflow confusion during setup, not a security issue.

### F7 — What is correctly consistent (for completeness)

- **Player-ID generation** is uniformly `require_sim_manager` across all mint and reset endpoints — coherent and correctly excludes project_admin and anonymous. No contradictions found in this flow.
- The role ladder is mirrored and drift-pinned (`test_role_hierarchy_sync.py`).
- `assignable_roles_for` correctly blocks god_mode assignment and caps project_admin — no privilege-escalation path found in role assignment.
- Cohort *ownership* on `/start` is correctly resolved from the JWT identity, not the request body (spoofing closed, `router.py:1010-1035`).

---

## 4. Recommended revisions

The unifying principle: **collapse the three authorization systems into one authoritative source (role + guards), and make anything that looks like an authority control either enforce or disappear.**

**R1 (for F1) — resolve the dead permissions dict. Pick ONE:**
- **R1a (recommended, lower risk):** treat role as the sole source of capability and **remove** the `permissions` dict from the create/edit UI and the login payload, leaving role the only lever. Simplest, matches how the system actually behaves, eliminates the misleading control.
- **R1b (higher effort):** make the permissions *real* — add a `require_capability("can_undo_rounds")` dependency and gate the corresponding endpoints on it, with role granting the defaults. Only worth it if per-facilitator capability tuning is genuinely wanted beyond role.

  Whichever is chosen, add a tripwire test asserting the decision (no orphan permission keys / every permission key has an enforcement site).

**R2 (for F2) — one rule for cohort creation.** Decide the intended policy — the two independent signals (permission default + registry-tab gate) both say *base facilitators do not create cohorts*, so the cleanest policy is **`require_lead_facilitator` (or the registry-admin set) on `/start`'s creation branch**. Enforce it server-side; make both UI surfaces read that same rule. Resume-of-existing-session must stay open to the owning player/facilitator — gate only the *create-new* branch.

**R3 (for F3) — use `is_admin_role`.** Replace the `is_admin_caller` expression with `is_admin_role(caller_role)`; drop the `caller_id == "god_mode"` id-check (redundant once role-based). One-line fix; add it to the existing "no `== 'super_admin'`" convention scan.

**R4 (for F4) — retire or align `/facilitators/batch`.** It is unused by the UI. Either delete it, or change its guard to `require_registry_admin` so all four creation paths share one authz rule. Deleting is cleaner.

**R5 (for F5) — clarify project_admin.** Keep the behaviour, fix the model: (a) add a one-line note at `assignable_roles_for` that project_admin's grants are provisioning delegation, not a level comparison; (b) decide whether registry project_admins are intended — if not, remove `"project_admin"` from `_ASSIGNABLE_ROLES` so it stays virtual-only; if yes, correct the "virtual" wording in the role doc.

**R6 (for F6) — state the seam.** Either document explicitly that project_admin provisions cohort shells and the owning facilitator populates the roster, or (if project_admin should fully stand up a cohort) move `generate-player` for a **not-yet-started** cohort to `require_facilitator`. Recommend documenting, not widening — keeping player mint as run-management is the safer default.

---

## 5. Implementation plan (prioritised, low-blast-radius first)

**Do NOT ship any of this immediately before a live workshop** — auth changes are the highest-regret category. Sequence after the current class.

| Phase | Items | Risk | Effort | Notes |
|---|---|---|---|---|
| **P0 — one-liners, safe** | R3 (`is_admin_role`), R4 (delete dead `/facilitators/batch`), R5a+R5 doc fixes | very low | ~1 hr | Pure corrections; add to the existing convention-scan test. |
| **P1 — the headline** | R1 (resolve inert permissions — recommend R1a removal) | low (R1a) / med (R1b) | 2–4 hr | R1a is deletion + payload trim; add a tripwire that fails if a permission key exists without an enforcement site. |
| **P2 — cohort-creation policy** | R2 (single server-side rule + both UIs read it) | medium | 3–5 hr | Requires a policy decision first (who may create cohorts). Gate only the create-new branch; regression-test resume + owner-scoping + quota. |
| **P3 — model clarity** | R5b (decide registry project_admin), R6 (document the provisioning/roster seam) | low | 1–2 hr | Mostly docs + one optional guard change. |

**Verification discipline for every phase** (matching this repo's standard): prove the *current* behaviour with a failing test first, apply the fix, add a **tripwire** asserting the shape that allowed the contradiction (e.g. "no authorization decision reads an unenforced permission key"; "cohort-create has exactly one server-side rule"), and mutation-test the tripwire. Run the full backend suite (chunked) + the frontend RBAC drift tests; confirm `test_role_hierarchy_sync` and `test_c3_project_admin_run_isolation` still pass.

**Single biggest win for the effort:** P0 + P1a. They remove the two things most likely to mislead an administrator — the alias/id-based admin check and the entire fake permissions surface — in well under a day, with almost no behavioural risk.

---

## 6. One-line verdict

The **role ladder is sound** and the **player-ID flow is clean**. The real problems are *parallel authority systems that disagree*: an inert per-facilitator permissions dict (F1), a cohort-creation capability decided three different ways (F2), and a stale admin check that drops the `admin` alias (F3). None are actively exploitable by an outsider — all are authenticated-staff correctness and clarity defects — but F1 and F2 will actively mislead anyone administering roles, and both are cheap to fix once the class is done.
